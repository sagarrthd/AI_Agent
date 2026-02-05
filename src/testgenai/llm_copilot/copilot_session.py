from __future__ import annotations

import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, WebDriverException


class CopilotSession:
    def __init__(self, profile_path: str, start_url: str) -> None:
        options = webdriver.EdgeOptions()
        if profile_path:
            options.add_argument(f"user-data-dir={profile_path}")
        self._driver = webdriver.Edge(options=options)
        self._start_url = start_url

    def open(self) -> None:
        self._driver.get(self._start_url)

    def send_prompt(self, prompt: str, timeout_s: int = 120) -> str:
        try:
            input_box = WebDriverWait(self._driver, 30).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )
            input_box.clear()
            input_box.send_keys(prompt)
            send_btn = self._driver.find_element(By.CSS_SELECTOR, "button[aria-label='Send']")
            send_btn.click()
            return self._wait_for_response(timeout_s)
        except (TimeoutException, WebDriverException) as exc:
            raise RuntimeError("Copilot automation failed") from exc

    def close(self) -> None:
        self._driver.quit()

    def _wait_for_response(self, timeout_s: int) -> str:
        end = time.time() + timeout_s
        stable_count = 0
        last_text = ""
        while time.time() < end:
            text = self._latest_response_text()
            if text and text == last_text:
                stable_count += 1
            else:
                stable_count = 0
                last_text = text

            if text and stable_count >= 2:
                return text
            time.sleep(1)
        raise TimeoutError("Copilot response timed out")

    def _latest_response_text(self) -> str:
        blocks = self._driver.find_elements(By.CSS_SELECTOR, ".copilot-response")
        return blocks[-1].text if blocks else ""
