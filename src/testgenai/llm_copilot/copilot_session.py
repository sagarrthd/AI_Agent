from __future__ import annotations

import time
import json
from typing import Optional, List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException


class CopilotSession:
    def __init__(self, profile_path: str = "", start_url: str = "", debug_port: int = 9222) -> None:
        self.options = webdriver.EdgeOptions()
        
        # KEY CHANGE: Connect to existing browser
        if debug_port:
            self.options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            print(f"🔌 Connecting to existing Edge via port {debug_port}...")
        elif profile_path:
            self.options.add_argument(f"user-data-dir={profile_path}")
            
        try:
            self._driver = webdriver.Edge(options=self.options)
        except WebDriverException as e:
            if "Chrome failed to start" in str(e) or "DevToolsActivePort file doesn't exist" in str(e):
                raise RuntimeError(
                    f"Could not connect to Edge on port {debug_port}. "
                    "Make sure you launched Edge with: msedge.exe --remote-debugging-port={debug_port}"
                ) from e
            raise e
            
        self._start_url = start_url

    def open(self) -> None:
        # If attaching, we might already be on the page. Check URL.
        try:
            if "copilot" not in self._driver.current_url.lower() and "bing.com" not in self._driver.current_url.lower():
                if self._start_url:
                    self._driver.get(self._start_url)
        except WebDriverException:
            # Connection might be lost or page closed
            pass

    def send_prompt(self, prompt: str, timeout_s: int = 180) -> str:
        """
        Robustly sends a prompt to Copilot and waits for the response.
        """
        driver = self._driver
        try:
            # 1. Find the Input Area (Shadow DOM or regular)
            # Copilot often uses Shadow DOM. We'll try a few strategies.
            input_box = self._find_input_box()
            if not input_box:
                raise RuntimeError("Could not find Copilot input box. Page structure may have changed.")
                
            # 2. Clear and Type
            # Sometimes .clear() doesn't work on rich text editors, use Ctrl+A, Del
            input_box.click()
            input_box.send_keys(Keys.CONTROL + "a")
            input_box.send_keys(Keys.DELETE)
            
            # Send keys in chunks to avoid bot detection/rate limits? No, paste is better for long text.
            # But selenium send_keys is fine for now.
            # For very large prompts, we might need to use JS to insert text.
            driver.execute_script("arguments[0].value = arguments[1];", input_box, prompt[:10]) # Force init
            input_box.send_keys(prompt)
            time.sleep(1) # Wait for UI to react
            
            # 3. Find Send Button is tricky. usually hitting ENTER works best.
            input_box.send_keys(Keys.ENTER)
            
            # Double check if we need to click a button
            # self._click_send_button() 
            
            print("✓ Prompt sent to Copilot. Waiting for generation...")
            return self._wait_for_response(timeout_s)
            
        except (TimeoutException, WebDriverException) as exc:
            # Capture screenshot for debug
            # driver.save_screenshot("copilot_error.png")
            raise RuntimeError(f"Copilot automation failed: {exc}") from exc

    def close(self) -> None:
        # If we attached, DO NOT quit() as it closes the user's browser!
        # Just close the connection by deleting the driver object?
        # Actually driver.quit() closes the session. driver.close() closes the tab.
        # If debugging, we probably shouldn't do either, just let it be.
        pass

    def _find_input_box(self):
        selectors = [
            "textarea#searchbox",
            "textarea[aria-label='Ask Copilot']",
            "textarea[name='q']",
            ".cib-serp-main textarea",
            "#searchbox"
        ]
        
        for sel in selectors:
            try:
                elems = self._driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    if e.is_displayed():
                        return e
            except:
                continue
                
        # Try Shadow DOM (simplified for now)
        return None

    def _wait_for_response(self, timeout_s: int) -> str:
        # Wait until "Stop Responding" button disappears or response stabilizes
        start_time = time.time()
        last_len = 0
        stable_iters = 0
        
        while time.time() - start_time < timeout_s:
            # Check if it's still generating
            is_generating = self._is_generating()
            
            text = self._latest_response_text()
            curr_len = len(text)
            
            if not is_generating and curr_len > 0:
                if curr_len == last_len:
                    stable_iters += 1
                else:
                    stable_iters = 0
                    
                if stable_iters > 3: # Stable for 3 seconds
                    return text
            
            last_len = curr_len
            time.sleep(1)
            
        if len(last_len) > 0:
             return self._latest_response_text() # Return what we have
             
        raise TimeoutError("Copilot generation timed out.")

    def _is_generating(self) -> bool:
        # Look for "Stop responding" button
        try:
            btns = self._driver.find_elements(By.TAG_NAME, "button")
            for b in btns:
                if "stop" in b.text.lower() or "responding" in b.text.lower():
                    return True
        except:
            pass
        return False

    def _latest_response_text(self) -> str:
        # Copilot (Bing Chat) structure is complex.
        # We need to find the LAST message that is FROM the bot.
        # This is a best-effort selector set.
        try:
            # Strategy 1: Look for cib-message-group (Shadow DOM hell usually)
            # Because accessing Shadow DOM in generic Selenium is hard, 
            # we rely on the fact that sometimes the text is accessible via aria-labels or specific containers.
            
            # Simple fallback: Get all text from the main container?
            # Let's try to grab all paragraphs and return the last big chunk.
            
            # NOTE: Getting text from Copilot is arguably the hardest part due to Shadow DOM.
            # We will use JavaScript to pierce Shadow DOM.
            
            script = """
            try {
                const hosts = document.querySelectorAll('.cib-serp-main');
                let lastText = "";
                // This is a simplified heuristic. 
                // A real robust script needs to traverse open shadow roots.
                return document.body.innerText; 
            } catch(e) { return ""; }
            """
            # Validating "document.body.innerText" is too noisy.
            # Let's try a specific known container if possible, or just user prompts.
            
            # BETTER STRATEGY: 
            # We will assume the user can copy-paste if automation fails? No, that defeats the point.
            # We will try to find specific bubbles.
            
            # Since I cannot see the current DOM, I will return the entire body text for now,
            # and the `response_parser` will have to utilize regex to find the JSON/Table.
            return self._driver.find_element(By.TAG_NAME, "body").text
            
        except Exception:
            return ""
