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
        self.root.title("TestGenAI - Automated Test Case Generator")
        self.root.geometry("1000x850")  # Increased size for AI options
        
        # Variables
        self.input_folder = tk.StringVar(value="")
        self.output_folder = tk.StringVar(value="")
        
        # AI Variables
        self.use_ai = tk.BooleanVar(value=False)
        self.ai_url = tk.StringVar(value="https://copilot.microsoft.com")
        self.browser_profile = tk.StringVar(value="")
        
        self.requirements_found = []
        self.is_processing = False
        
        # Colors
        self.bg_color = "#f0f0f0"
        self.accent_color = "#0066cc"
        self.success_color = "#28a745"
        self.error_color = "#dc3545"
        
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
        title_frame = tk.Frame(self.root, bg=self.accent_color, height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🚀 TestGenAI", font=("Arial", 24, "bold"), bg=self.accent_color, fg="white").pack(pady=10)
        tk.Label(title_frame, text="Automated Test Case & Traceability Generator", font=("Arial", 11), bg=self.accent_color, fg="white").pack()
        
        # Main Scrollable Content
        main_canvas = tk.Canvas(self.root, bg=self.bg_color)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.bg_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content Wrapper
        content_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # --- Input Section ---
        self.create_section(content_frame, "📁 Input Files Location", self.input_folder, self.browse_input_folder, 
                           "Select folder containing requirements files (.txt, .docx, .pdf):")
        self.files_label = tk.Label(content_frame, text="No folder selected", font=("Arial", 9, "italic"), bg=self.bg_color, fg="#666")
        self.files_label.pack(anchor=tk.W, padx=20, pady=(0, 15))

        # --- Output Section ---
        self.create_section(content_frame, "💾 Output Location", self.output_folder, self.browse_output_folder,
                           "Select folder to save generated test plan:")
        
        # --- AI / Copilot Section ---
        ai_section = tk.LabelFrame(content_frame, text="🤖 AI / Copilot Settings", font=("Arial", 11, "bold"), bg=self.bg_color, fg="#333")
        ai_section.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        ai_inner = tk.Frame(ai_section, bg=self.bg_color)
        ai_inner.pack(fill=tk.X, padx=10, pady=10)
        
        # Checkbox
        tk.Checkbutton(ai_inner, text="Enable AI Generation (Microsoft Copilot)", variable=self.use_ai, 
                      command=self.toggle_ai_options, font=("Arial", 10, "bold"), bg=self.bg_color).pack(anchor=tk.W)
        
        # Warning if deps missing
        if not HAS_LLM_DEPS:
            tk.Label(ai_inner, text="⚠ AI dependencies (selenium) not installed. AI features disabled.", 
                    fg=self.error_color, bg=self.bg_color, font=("Arial", 9)).pack(anchor=tk.W, pady=(0, 5))
            self.use_ai.set(False)
        
        # AI Options Frame
        self.ai_options_frame = tk.Frame(ai_inner, bg=self.bg_color)
        self.ai_options_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Copilot URL
        tk.Label(self.ai_options_frame, text="Copilot URL:", bg=self.bg_color).pack(anchor=tk.W)
        tk.Entry(self.ai_options_frame, textvariable=self.ai_url, font=("Arial", 10)).pack(fill=tk.X, pady=(0, 10))
        
        # Browser Profile
        tk.Label(self.ai_options_frame, text="Edge Browser Profile Path (Required for signed-in session):", bg=self.bg_color).pack(anchor=tk.W)
        profile_frame = tk.Frame(self.ai_options_frame, bg=self.bg_color)
        profile_frame.pack(fill=tk.X)
        tk.Entry(profile_frame, textvariable=self.browser_profile, font=("Arial", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(profile_frame, text="Examples?", command=self.show_profile_help, bg="#ddd", relief=tk.FLAT).pack(side=tk.LEFT, padx=(5,0))
        
        if not self.use_ai.get():
            self.toggle_ai_options() # Hide initially

        # --- Progress Log ---
        log_section = tk.LabelFrame(content_frame, text="📊 Activity Log", font=("Arial", 11, "bold"), bg=self.bg_color)
        log_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(log_section, height=12, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)

        # --- Buttons ---
        btn_frame = tk.Frame(content_frame, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.generate_btn = tk.Button(btn_frame, text="🚀 Generate Test Cases", command=self.generate_tests,
                                     font=("Arial", 12, "bold"), bg=self.success_color, fg="white", padx=30, pady=10)
        self.generate_btn.pack(side=tk.LEFT)
        
        tk.Button(btn_frame, text="❌ Exit", command=self.root.quit, font=("Arial", 10), bg=self.error_color, fg="white", padx=20, pady=10).pack(side=tk.RIGHT)

        self.log("Ready. Please select Input and Output folders.")

    def create_section(self, parent, title, var, browse_cmd, instruction):
        frame = tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), bg=self.bg_color)
        frame.pack(fill=tk.X, pady=(0, 5), padx=5)
        inner = tk.Frame(frame, bg=self.bg_color)
        inner.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(inner, text=instruction, bg=self.bg_color).pack(anchor=tk.W)
        path_frame = tk.Frame(inner, bg=self.bg_color)
        path_frame.pack(fill=tk.X)
        tk.Entry(path_frame, textvariable=var, font=("Arial", 10), state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Button(path_frame, text="Browse...", command=browse_cmd, bg=self.accent_color, fg="white", padx=15).pack(side=tk.LEFT)

    def toggle_ai_options(self):
        if self.use_ai.get():
            if not HAS_LLM_DEPS:
                messagebox.showerror("Missing Dependencies", "Selenium is required for AI features but is not installed.\nPlease run: pip install selenium")
                self.use_ai.set(False)
                return
            state = 'normal'
        else:
            state = 'disabled'

        def set_state_recursive(widget):
            try:
                widget.configure(state=state)
            except tk.TclError:
                # Some widgets (like Frame, Label) don't support the state option
                pass
            
            for child in widget.winfo_children():
                set_state_recursive(child)

        set_state_recursive(self.ai_options_frame)

    def show_profile_help(self):
        msg = ("To use Copilot, you need a signed-in Edge browser session.\n\n"
               "Typical Profile Paths:\n"
               "Windows: C:/Users/<User>/AppData/Local/Microsoft/Edge/User Data/Default\n\n"
               "Tip: Go to edge://version in Edge and look for 'Profile Path'.")
        messagebox.showinfo("Browser Profile Help", msg)

    def browse_input_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.input_folder.set(f)
            self.scan_input_folder(f)

    def browse_output_folder(self):
        f = filedialog.askdirectory()
        if f: self.output_folder.set(f)

    def scan_input_folder(self, folder):
        p = Path(folder)
        files = []
        for ext in ['*.txt', '*.md', '*.docx', '*.pdf', '*.xlsx']:
            files.extend(list(p.glob(ext)))
        self.template_file = None
        self.requirements_found = []
        
        if files:
            # Separate Template from Requirements
            req_files = []
            for f in files:
                if "template" in f.name.lower() and f.suffix.lower() == ".xlsx":
                    self.template_file = f
                else:
                    req_files.append(f)
            
            self.requirements_found = req_files
            
            msg = f"✓ Found {len(req_files)} requirement file(s)"
            if self.template_file:
                msg += f"\n✓ Found Template: {self.template_file.name}"
                
            self.files_label.config(text=msg, fg=self.success_color)
            self.log(f"Found {len(req_files)} requirement files.")
            if self.template_file:
                self.log(f"Using Test Template: {self.template_file.name}")
        else:
            self.files_label.config(text="⚠ No supported files found (.txt, .md, .docx, .pdf, .xlsx)", fg=self.error_color)
            self.log("⚠ No supported files found in the selected folder!", "warning")

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
            messagebox.showerror("Error", "Please select both Input and Output folders.")
            return
        if not self.requirements_found:
            messagebox.showerror("Error", "No valid requirement files found in input folder.")
            return

        self.generate_btn.config(state=tk.DISABLED, text="⏳ Generating...")
        threading.Thread(target=self.run_generation, daemon=True).start()

    def run_generation(self):
        try:
            self.log("Staring generation process...", "info")
            if self.template_file:
                self.log(f"Strictly following template: {self.template_file.name}", "info")
            
            # 1. Load Requirements
            all_reqs = []
            for f in self.requirements_found:
                self.log(f"Reading: {f.name}...")
                reqs = load_requirements(str(f))
                if not reqs:
                    self.log(f"⚠ Warning: No requirements found in {f.name}. File might be empty or unreadable.", "warning")
                all_reqs.extend(reqs)
            
            if not all_reqs:
                raise ValueError("No requirements extracted from any files! Check input file formats.")

            requirements = [Requirement(req_id=r["req_id"], title=r["title"], description=r["description"], req_type=r.get("req_type", "functional")) for r in all_reqs]
            self.log(f"✓ Loaded {len(requirements)} total requirements.", "success")

            # 2. Generate Baseline Tests (Rule Engine)
            self.log("Running Rule Engine...", "info")
            engine = RuleEngine()
            tests = engine.build_baseline_tests(requirements)
            self.log(f"✓ Rule Engine generated {len(tests)} tests.", "success")

            # 3. AI Generation (Optional)
            if self.use_ai.get() and HAS_LLM_DEPS:
                self.log("🤖 Starting AI Copilot generation...", "info")
                try:
                    copilot = CopilotSession(self.browser_profile.get(), self.ai_url.get())
                    self.log("Opening browser...", "info")
                    copilot.open()
                    
                    # Convert Requirement objects back to dicts for the prompt builder
                    req_dicts_for_prompt = [ {"req_id": r.req_id, "description": r.description} for r in requirements ]
                    
                    self.log(f"Sending {len(requirements)} requirements to Copilot...", "info")
                    prompt = build_prompt(req_dicts_for_prompt, [], "") # No signals for now
                    
                    response_text = copilot.send_prompt(prompt, timeout_s=120)
                    self.log("✓ Received response from Copilot.", "success")
                    copilot.close()
                    
                    ai_tests_data = parse_table_response(response_text)
                    self.log(f"✓ AI returned {len(ai_tests_data)} new test cases.", "success")
                    
                    # Convert AI response to TestCase objects
                    # Import here to access helper or duplicate logic? Let's use pipeline's helper if possible or simple logic
                    from testgenai.orchestration.pipeline import _rows_to_tests
                    ai_test_objects = _rows_to_tests(ai_tests_data)
                    tests.extend(ai_test_objects)
                    
                except Exception as e:
                    self.log(f"❌ AI Generation Failed: {e}", "error")
                    self.log("Continuing with only Rule-based tests...", "warning")

            # 4. Save Output
            out_path = Path(self.output_folder.get())
            if not out_path.exists():
                out_path.mkdir(parents=True, exist_ok=True)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"TestPlan_{timestamp}.xlsx"
            full_path = out_path / filename
            
            trace = build_trace_matrix(requirements, tests)
            
            self.log(f"Saving to {filename}...", "info")
            
            # Pass the template file if found
            template_path = str(self.template_file) if self.template_file else ""
            
            write_stp_output(template_path, str(full_path), tests, trace, "Traceability")
            
            self.log("-" * 50)
            self.log("SUCCESS! Generation Complete.", "success")
            self.log(f"Total Tests: {len(tests)}")
            self.log(f"File Saved: {full_path}")
            
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Generated {len(tests)} test cases.\nSaved to:\n{full_path}"))
            self.root.after(0, lambda: self.ask_open(full_path))

        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}", "error")
            self.root.after(0, lambda: messagebox.showerror("Execution Failed", str(e)))
        finally:
            self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL, text="🚀 Generate Test Cases"))

    def ask_open(self, path):
        if messagebox.askyesno("Open File", "Open the generated Test Plan now?"):
            import os
            os.startfile(str(path))

if __name__ == "__main__":
    root = tk.Tk()
    app = TestGenAIGUI(root)
    root.mainloop()
