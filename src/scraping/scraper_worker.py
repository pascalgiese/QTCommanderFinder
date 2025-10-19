import json
import bs4
from PyQt5.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_stealth import stealth

from config.constants import DEBUG_SCREENSHOT_PATH_TPL, DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH


class DecklistScraperWorker(QObject):
    """
    Runs Selenium in a separate thread to avoid freezing the GUI.
    Scrapes decklists from supported websites (Moxfield, Archidekt).
    """
    finished = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        if "moxfield.com" in self.url:
            self.site = "moxfield"
        elif "archidekt.com" in self.url:
            self.site = "archidekt"
        else:
            self.site = "unknown"

    def run(self):
        """The long-running task."""
        # --- Driver Setup ---
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")  # Absolutely necessary for running as root/in a container
        options.add_argument("--disable-dev-shm-usage")  # Overcomes limited resource problems
        options.add_argument("--disable-gpu")  # Applicable to headless browser
        options.add_argument("--remote-debugging-port=9222") # Optional, but can improve stability
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)

        stealth(driver,
              languages=["en-US", "en"],
              vendor="Google Inc.",
              platform="Win32",
              webgl_vendor="Intel Inc.",
              renderer="Intel Iris OpenGL Engine",
              fix_hairline=True,
              )
        driver.get(self.url)
        try:
            if self.site == "moxfield":
                self._scrape_moxfield(driver)
            elif self.site == "archidekt":
                self._scrape_archidekt(driver)
            else:
                self.finished.emit(f"Error: Unsupported website for scraping: {self.url}")

        except TimeoutException as e: # Specific exception for timeouts
            error_message = f"Error: Timed out on {self.site.capitalize()}. Check selectors or page load."
            print(f"--- SELENIUM DEBUG: TIMEOUT ---")
            print(f"Error message: {e}")
            driver.save_screenshot(DEBUG_SCREENSHOT_PATH_TPL.format(site=self.site))
            print(f"Screenshot saved to {DEBUG_SCREENSHOT_PATH_TPL.format(site=self.site)}")
            self.finished.emit(error_message)
        except Exception as e: # Catch-all for any other unexpected errors
            error_message = f"An unexpected error occurred: {type(e).__name__}: {e}"
            print(f"--- SELENIUM DEBUG: UNEXPECTED ERROR ---")
            print(error_message)
            driver.save_screenshot(DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH)
            print(f"Screenshot saved to {DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH}")
            self.finished.emit(error_message)
        finally:
            driver.quit()

    def _scrape_moxfield(self, driver):
        """Scrapes the decklist from a Moxfield page."""
        more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "subheader-more"))
        )
        driver.execute_script("arguments[0].click();", more_button)

        export_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Export"))
        )
        driver.execute_script("arguments[0].click();", export_link)

        textarea = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "form-control"))
        )
        decklist = textarea.get_attribute('value')
        self.finished.emit(decklist)

    def _scrape_archidekt(self, driver):
        """Scrapes an Archidekt decklist by parsing the embedded __NEXT_DATA__ JSON."""
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
        soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        if not next_data_script:
            self.finished.emit("Error: Could not find __NEXT_DATA__ script tag on Archidekt.")
            return
        data = json.loads(next_data_script.string)
        card_map = data.get('props', {}).get('pageProps', {}).get('redux', {}).get('deck', {}).get("cardMap", {})
        if not card_map:
            self.finished.emit("Error: Could not find card list (cardMap) in Archidekt's page data.")
            return
        decklist_lines = []
        for card_item in sorted(card_map.values(), key=lambda c: c.get('name', '')):
            if "Maybeboard" not in card_item.get('categories', []):
                line = f"{card_item.get('qty')} {card_item.get('name')} ({card_item.get('setCode')}) {card_item.get('collectorNumber')}"
                if "Commander" in card_item.get('categories', []):
                    decklist_lines.insert(0, line)
                else:
                    decklist_lines.append(line)
        self.finished.emit("\n".join(decklist_lines))