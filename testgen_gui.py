#!/usr/bin/env python3
"""
TestGenAI - Graphical User Interface
A user-friendly interface for automated test case generation with AI support
"""
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
from datetime import datetime

sys.path.insert(0, 'src')

from testgenai.ingestion.doc_parser import load_requirements
from testgenai.models.requirement import Requirement
from testgenai.rules.rule_engine import RuleEngine
from testgenai.mapping.traceability import build_trace_matrix
from testgenai.reports.stp_writer import write_stp_output
# Lazy import for Copilot to avoid crashing if dependencies are missing
try:
    from testgenai.llm_copilot.copilot_session import CopilotSession
    from testgenai.llm_copilot.prompt_builder import build_prompt
    from testgenai.llm_copilot.response_parser import parse_table_response
    HAS_LLM_DEPS = True
except ImportError:
    HAS_LLM_DEPS = False


class TestGenAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TestGenAI - Enterprise Agent")
        self.root.geometry("1100x850")
        
        # Variables
        self.input_folder = tk.StringVar(value="")
        self.template_path = tk.StringVar(value="")
        self.output_folder = tk.StringVar(value="")
        
        # AI Variables
        self.use_ai = tk.BooleanVar(value=True)
        self.ai_url = tk.StringVar(value="https://copilot.microsoft.com")
        self.debug_port = tk.IntVar(value=9222)
        
        self.requirements_found = []
        self.is_processing = False
        
        # Colors
        self.bg_color = "#f4f6f9"
        self.accent_color = "#2c3e50"
        self.header_color = "#34495e"
        self.success_color = "#27ae60"
        self.error_color = "#c0392b"
        self.warning_color = "#d35400"
        
        self.root.configure(bg=self.bg_color)
        self.create_widgets()
        self.center_window()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg=self.header_color, height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🚀 TestGenAI Enterprise", font=("Segoe UI", 20, "bold"), bg=self.header_color, fg="white").pack(pady=(15,5))
        tk.Label(title_frame, text="Generate ISO 26262 Compliant Test Cases with AI", font=("Segoe UI", 10), bg=self.header_color, fg="#ecf0f1").pack()
        
        # Main Canvas
        main_canvas = tk.Canvas(self.root, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.bg_color)
        
        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        content = tk.Frame(scrollable_frame, bg=self.bg_color)
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # --- 1. Requirements Input ---
        self.create_path_section(content, "1. Requirements Input", self.input_folder, self.browse_input_folder, 
            "Select folder containing requirement docs (.txt, .docx, .pdf, .xlsx):")
        self.files_label = tk.Label(content, text="No folder selected", font=("Segoe UI", 9, "italic"), bg=self.bg_color, fg="#7f8c8d")
        self.files_label.pack(anchor=tk.W, padx=20, pady=(0, 20))

        # --- 2. Master Template ---
        self.create_path_section(content, "2. Master Test Template (STP)", self.template_path, self.browse_template_file,
            "Select the Excel Template (.xlsx) to fill:")

        # --- 3. Output Location ---
        self.create_path_section(content, "3. Output Location", self.output_folder, self.browse_output_folder,
            "Select folder to save the generated Test Plan:")
        
        # --- 4. AI Engine ---
        ai_frame = tk.LabelFrame(content, text="4. AI Engine (Copilot)", font=("Segoe UI", 11, "bold"), bg=self.bg_color, fg=self.header_color)
        ai_frame.pack(fill=tk.X, pady=(0, 20), padx=5)
        
        ai_inner = tk.Frame(ai_frame, bg=self.bg_color)
        ai_inner.pack(fill=tk.X, padx=15, pady=15)
        
        # Checkbox
        tk.Checkbutton(ai_inner, text="Enable AI Generation", variable=self.use_ai, 
                      font=("Segoe UI", 10, "bold"), bg=self.bg_color, activebackground=self.bg_color).pack(anchor=tk.W)
        
        help_text = ("This mode connects to an EXISTING Edge browser session to avoid Captchas.\n"
                     "1. Click 'Launch Browser & Login'.\n"
                     "2. Log in to Copilot manually.\n"
                     "3. Click 'Generate' below.")
        tk.Label(ai_inner, text=help_text, justify=tk.LEFT, bg="#e8f6f3", fg="#16a085", relief=tk.SOLID, borderwidth=1, padx=10, pady=5).pack(anchor=tk.W, fill=tk.X, pady=10)
        
        btn_launch = tk.Button(ai_inner, text="🌐 Launch Browser & Login", command=self.launch_browser_debug,
                              bg="#2980b9", fg="white", font=("Segoe UI", 10, "bold"), padx=15, pady=5, relief=tk.FLAT)
        btn_launch.pack(anchor=tk.W)

        # --- Logs ---
        log_frame = tk.LabelFrame(content, text="Activity Log", font=("Segoe UI", 11, "bold"), bg=self.bg_color, fg=self.header_color)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 20))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=("Consolas", 9), relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # --- Action Buttons ---
        btn_row = tk.Frame(content, bg=self.bg_color)
        btn_row.pack(fill=tk.X, pady=10)
        
        self.generate_btn = tk.Button(btn_row, text="⚡ Generate Test Cases", command=self.generate_tests,
                                     font=("Segoe UI", 12, "bold"), bg=self.success_color, fg="white", padx=40, pady=12, relief=tk.FLAT)
        self.generate_btn.pack(side=tk.LEFT)
        
        tk.Button(btn_row, text="Exit", command=self.root.quit, font=("Segoe UI", 10), bg="#95a5a6", fg="white", padx=20, pady=12, relief=tk.FLAT).pack(side=tk.RIGHT)

    def create_path_section(self, parent, title, var, cmd, desc):
        frame = tk.LabelFrame(parent, text=title, font=("Segoe UI", 11, "bold"), bg=self.bg_color, fg=self.header_color)
        frame.pack(fill=tk.X, pady=(0, 5), padx=5)
        path_row = tk.Frame(frame, bg=self.bg_color)
        path_row.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(path_row, text=desc, bg=self.bg_color, font=("Segoe UI", 9)).pack(anchor=tk.W)
        
        entry_row = tk.Frame(path_row, bg=self.bg_color)
        entry_row.pack(fill=tk.X, pady=(5,0))
        
        tk.Entry(entry_row, textvariable=var, font=("Segoe UI", 10), state="readonly", relief=tk.FLAT, bg="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=4)
        tk.Button(entry_row, text="Browse...", command=cmd, bg=self.accent_color, fg="white", padx=15, relief=tk.FLAT).pack(side=tk.LEFT)

    def browse_input_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.input_folder.set(f)
            self.scan_reqs(f)

    def browse_template_file(self):
        f = filedialog.askopenfilename(filetypes=[("Excel Template", "*.xlsx")])
        if f: self.template_path.set(f)

    def browse_output_folder(self):
        f = filedialog.askdirectory()
        if f: self.output_folder.set(f)

    def launch_browser_debug(self):
        import subprocess
        try:
            subprocess.Popen("launch_edge_debug.bat", shell=True)
            self.log("Browser launched. Please log in manually.", "info")
        except Exception as e:
            self.log(f"Failed to launch browser: {e}", "error")

    def scan_reqs(self, folder):
        p = Path(folder)
        files = []
        for ext in ['*.txt', '*.md', '*.docx', '*.pdf', '*.xlsx']:
            files.extend(list(p.glob(ext)))
        
        # Exclude the selected template if it's in the same folder?
        # Just warn user if they pick the same file.
        
        self.requirements_found = files
        if files:
            self.files_label.config(text=f"✓ Found {len(files)} requirement files.", fg=self.success_color)
            self.log(f"Found {len(files)} files in input folder.")
        else:
            self.files_label.config(text="⚠ No supported files found.", fg=self.error_color)

    def log(self, msg, level="info"):
        self.log_text.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "❌" if level == "error" else "⚠" if level == "warning" else "✓" if level == "success" else "ℹ"
        self.log_text.insert(tk.END, f"[{ts}] {prefix} {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def generate_tests(self):
        if not self.input_folder.get() or not self.output_folder.get():
            messagebox.showerror("Missing Info", "Please select Input Folder and Output Folder.")
            return
        # Warn if no template
        if not self.template_path.get():
            if not messagebox.askyesno("No Template", "No Template selected. Steps will be generic and formatting lost.\nContinue?"):
                return

        self.generate_btn.config(state=tk.DISABLED, text="⏳ Generating...")
        threading.Thread(target=self.run_generation, daemon=True).start()

    def run_generation(self):
        try:
            self.log("Starting Generation Process...", "info")
            
            # 1. Load Requirements
            all_reqs = []
            for f in self.requirements_found:
                # Skip if it is the template file itself
                if self.template_path.get() and Path(f).resolve() == Path(self.template_path.get()).resolve():
                    continue
                    
                self.log(f"Reading: {f.name}...")
                reqs = load_requirements(str(f))
                all_reqs.extend(reqs)
            
            if not all_reqs:
                raise ValueError("No requirements found! Check your input folder.")
                
            requirements = [
                Requirement(
                    req_id=r["req_id"], 
                    title=r["title"], 
                    description=r["description"],
                    req_type=r.get("req_type", "functional")
                ) 
                for r in all_reqs
            ]
            self.log(f"✓ Loaded {len(requirements)} requirements.", "success")
            
            tests = []
            
            # 2. AI Generation
            if self.use_ai.get() and HAS_LLM_DEPS:
                self.log("🤖 Connecting to AI (Edge Debug Port 9222)...", "info")
                try:
                    # Connect to existing browser
                    copilot = CopilotSession(debug_port=self.debug_port.get())
                    self.log("✓ Connected to Browser Session.", "success")
                    
                    # Send prompt
                    req_dicts = [{"req_id": r.req_id, "description": r.description} for r in requirements]
                    
                    # TODO: Use upgraded prompt builder here
                    prompt = build_prompt(req_dicts, [], "") 
                    
                    self.log(f"Sending {len(requirements)} requirements to AI...", "info")
                    response_text = copilot.send_prompt(prompt, timeout_s=300) # Longer timeout
                    copilot.close() # Detach
                    
                    self.log("✓ Received AI Response.", "success")
                    
                    ai_tests_data = parse_table_response(response_text)
                    self.log(f"✓ AI returned {len(ai_tests_data)} test cases.", "success")
                    
                    from testgenai.orchestration.pipeline import _rows_to_tests
                    tests = _rows_to_tests(ai_tests_data)
                    
                except Exception as e:
                    self.log(f"❌ AI Failed: {e}", "error")
                    self.log("Falling back to Rule Engine...", "warning")
            
            # 3. Fallback / Rule Engine
            if not tests:
                engine = RuleEngine()
                tests = engine.build_baseline_tests(requirements)
                self.log("Generated baseline tests (Rule Engine).", "info")
            
            # 4. Save using strict template writer
            out_path = Path(self.output_folder.get())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"TestPlan_{timestamp}.xlsx"
            full_path = out_path / filename
            
            trace = build_trace_matrix(requirements, tests)
            
            self.log(f"Saving to {filename}...", "info")
            write_stp_output(self.template_path.get(), str(full_path), tests, trace, "Traceability")
            
            self.log("-" * 50)
            self.log("SUCCESS!", "success")
            self.root.after(0, lambda: messagebox.showinfo("Done", f"Saved to:\n{full_path}"))
            self.root.after(0, lambda: self.ask_open(full_path))
            
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}", "error")
            self.root.after(0, lambda: messagebox.showerror("Failed", str(e)))
        finally:
             self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL, text="⚡ Generate Test Cases"))

    def ask_open(self, path):
        if messagebox.askyesno("Open File", "Open the generated Test Plan?"):
            import os
            os.startfile(str(path))

if __name__ == "__main__":
    root = tk.Tk()
    app = TestGenAIGUI(root)
    root.mainloop()
