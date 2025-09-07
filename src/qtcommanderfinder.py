import os
import re
import sys
import json
import webbrowser
import pyperclip
import requests
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
import bs4
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QLineEdit, \
    QPushButton, QLayout, QMessageBox, QGridLayout
from PyQt5.QtGui import QPalette, QColor, QPixmap, QIcon
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_stealth import stealth

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In development, use the script's directory
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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
        # This is a simplified example. For production, you'd want to manage the driver path.
        # Also, consider headless mode: options.add_argument("--headless")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless") # Run in background without opening a window
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)

        # Apply selenium-stealth to bypass bot detection like Cloudflare
        # This must be done AFTER initializing the driver, but BEFORE the first .get() call.
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
            driver.save_screenshot(f"debug_screenshot_{self.site}.png")
            print(f"Screenshot saved to debug_screenshot_{self.site}.png")
            self.finished.emit(error_message)
        except Exception as e: # Catch-all for any other unexpected errors
            error_message = f"An unexpected error occurred: {type(e).__name__}: {e}"
            print(f"--- SELENIUM DEBUG: UNEXPECTED ERROR ---")
            print(error_message)
            driver.save_screenshot(f"debug_screenshot_unexpected_error.png")
            print(f"Screenshot saved to debug_screenshot_unexpected_error.png")
            self.finished.emit(error_message)
        finally:
            driver.quit()

    def _scrape_moxfield(self, driver):
        """Scrapes the decklist from a Moxfield page."""
        # Step 1: Wait for the "More" button to be clickable and click it.
        more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "subheader-more"))
        )
        driver.execute_script("arguments[0].click();", more_button)

        # Step 2: Wait for the "Export" link in the dropdown to be clickable and click it.
        export_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Export"))
        )
        driver.execute_script("arguments[0].click();", export_link)

        # Step 3: Wait for the textarea in the modal to appear and get its content.
        textarea = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "form-control"))
        )
        decklist = textarea.get_attribute('value')
        self.finished.emit(decklist)

    def _scrape_archidekt(self, driver):
        """Scrapes an Archidekt decklist by parsing the embedded __NEXT_DATA__ JSON."""
        # We wait a moment to ensure the page and the __NEXT_DATA__ script are fully loaded.
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

        # Get the HTML source code of the page
        soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})

        if not next_data_script:
            self.finished.emit("Error: Could not find __NEXT_DATA__ script tag on Archidekt.")
            return

        data = json.loads(next_data_script.string)

        # Navigate through the JSON structure to get to the card list
        # Correct path and correct data structure (dict of dicts)
        card_map = data.get('props', {}).get('pageProps', {}).get('redux', {}).get('deck', {}).get("cardMap", {})

        if not card_map:
            self.finished.emit("Error: Could not find card list (cardMap) in Archidekt's page data.")
            return

        # Format the decklist
        decklist_lines = []
        # Since card_map is a dictionary, we iterate over its values.
        card_list = list(card_map.values())

        # Sort the cards by name for a consistent output
        sorted_cards = sorted(card_list, key=lambda c: c.get('name', ''))

        for card_item in sorted_cards:
            quantity = card_item.get('qty')
            card_name = card_item.get('name')
            if quantity and card_name:
                decklist_lines.append(f"{quantity} {card_name}")

        self.finished.emit("\n".join(decklist_lines))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        #--- DATA CACHE ---#
        self.data = {}
        self.original_commander_pixmap = None
        self.original_partner_pixmap = None
        self.filepath_front = None
        self.filepath_back = None
        self.times_clicked_flip = 0

        #--- WINDOW SETTINGS ---#
        self.setWindowTitle("QTCommanderFinder")
        self.setMinimumSize(800, 800)
        icon_path = resource_path(os.path.join("assets", "flash-cards.png"))
        self.setWindowIcon(QIcon(icon_path))

        # --- THREADING ---#
        self.thread = None
        self.worker = None

        # --- TEXT SEARCH BAR ---#
        self.searchText = QLineEdit()
        self.searchText.setPlaceholderText("Search a commander...")
        self.searchText.setFixedWidth(200)

        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.search)

        self.randomButton = QPushButton("Random")
        self.randomButton.clicked.connect(self.search_random)

        # --- SEARCHBAR LAYOUT ---#
        self.searchMenuLayout = QHBoxLayout()
        self.searchMenuLayout.addWidget(self.searchText)
        self.searchMenuLayout.addWidget(self.searchButton)
        self.searchMenuLayout.addWidget(self.randomButton)

        #--- EXTENDED SEARCH BAR ---#
        self.price_limit = QLineEdit()
        self.price_limit.setPlaceholderText("Enter your budget")
        self.price_limit.setFixedWidth(400)
        self.budget_hint = QLabel(
            "Budget search allows minus-separated ranges, min values with >, and max values with <")
        self.partnerSearch = QCheckBox("Search Partner Combo")
        self.partnerSearch.setFixedWidth(self.partnerSearch.sizeHint().width())
        self.helpButton = QPushButton("Syntax Guide")
        self.helpButton.clicked.connect(self.show_syntax_guide)

        #--- EXTENDED SEARCH CONTAINER ---#
        self.extendedSearchLayout = QGridLayout()
        self.extendedSearchLayout.setContentsMargins(0,0,0,0)
        self.extendedSearchLayout.setSpacing(0)
        self.extendedSearchLayout.addWidget(self.price_limit, 0, 0, Qt.AlignLeft)
        self.extendedSearchLayout.addWidget(self.budget_hint, 1, 0, Qt.AlignTop)
        self.extendedSearchLayout.addWidget(self.partnerSearch, 0, 1, Qt.AlignLeft)
        self.extendedSearchLayout.addWidget(self.helpButton, 0, 2, Qt.AlignLeft)

        #--- IMAGE WIDGETS ---#
        self.commanderImage = QLabel(self)
        self.commanderImage.setAlignment(Qt.AlignCenter)
        self.partnerImage = QLabel(self)
        self.partnerImage.setAlignment(Qt.AlignCenter)
        self.partnerImage.setVisible(False)
        self.commanderImageFlip = QPushButton("Flip")
        self.commanderImageFlip.setFixedSize(50,40)
        self.commanderImageFlip.clicked.connect(self.flip_image)
        self.commanderImageFlip.setEnabled(False)
        self.commanderImageFlip.setVisible(False)

        #--- IMAGE CONTAINER ---#
        self.imageLayout = QGridLayout()
        self.imageLayout.addWidget(self.commanderImage, 1, 0, Qt.AlignCenter)
        self.imageLayout.addWidget(self.partnerImage, 1, 1, Qt.AlignCenter)
        self.imageLayout.addWidget(self.commanderImageFlip, 0, 1)

        #--- ACTION BUTTONS ---#
        self.get_Decklist = QPushButton("Get Decklist")
        self.get_Decklist.clicked.connect(self.fetch_first_decklist_in_budget)
        self.deckPriceLabel = QLabel()
        self.deckPriceLabel.setEnabled(False)
        self.deckPriceLabel.setAlignment(Qt.AlignCenter)

        #--- ACTION BUTTON CONTAINER ---#
        self.actionLayout = QVBoxLayout()
        self.actionLayout.addWidget(self.get_Decklist)
        self.actionLayout.addWidget(self.deckPriceLabel)

        #--- ERROR BOX ---#
        self.errorLabel = QLabel()
        self.errorLabel.setEnabled(False)
        self.errorLabel.setVisible(False)
        self.errorLabel.setAlignment(Qt.AlignCenter)
        self.errorLabel.setStyleSheet("color: black; background-color: red;")

        #--- ERROR BOX CONTAINER ---#
        self.errorLayout = QHBoxLayout()
        self.errorLayout.addWidget(self.errorLabel)

        #--- FINAL LAYOUT ---#
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.searchMenuLayout)
        self.layout.addLayout(self.extendedSearchLayout)
        self.layout.addLayout(self.imageLayout)
        self.layout.addLayout(self.actionLayout)
        self.layout.addLayout(self.errorLayout)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

    def search (self):

        # --- MAKE SURE THERE IS NO OLD BACK AND PARTNER LEFT ---#
        if os.path.isfile("commander_back.png"):
            os.remove("commander_back.png")
        if os.path.isfile("partner.png"):
            os.remove("partner.png")

        #--- RESET PARTNER VIEW ---#
        self.partnerImage.setVisible(False)
        self.original_partner_pixmap = None

        #--- RESET FLIP COUNT AND BUTTON ---#
        self.times_clicked_flip = 0
        self.commanderImageFlip.setVisible(False)
        self.commanderImageFlip.setEnabled(False)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "application/json;q=0.9,*/*;q=0.8"
        }

        query = f"{self.searchText.text()}"
        # Add "is:commander" to find only legendary creatures that are legal as commanders.
        if "is:commander" not in query.lower():
            query += " is:commander"
        if "game:paper" not in query.lower():
            query += " game:paper"
        if self.partnerSearch.isChecked():
            query += " o:partner"

        payload = {
            "order": "edhrec",
            "q": query
        }
        base_url = "https://api.scryfall.com/cards/search"

        try:
            response = requests.get(base_url, params=payload, headers=headers)
            time.sleep(0.1)
            response.raise_for_status()  # Raises an error for 4xx/5xx responses
            json_data = response.json().get('data')

            if not json_data:
                print("No cards found for this search.")
                self.commanderImage.setText("Commander not found.")
                return

            commander = json_data[0]
            self.data['commander'] = commander

            if self.partnerSearch.isChecked():
                print(f"Looking up most popular partner for {commander.get('name')}...")
                edhrec_link = commander.get("related_uris", {}).get("edhrec")
                if not edhrec_link:
                    print("No EDHRec link found.")
                    return
                response_edhrec = requests.get(edhrec_link)
                response_edhrec.raise_for_status()
                deck_slug = response_edhrec.url
                name_slug = deck_slug.rsplit("/", 1)[-1]
                name_slug = name_slug.replace("?cc=", "")
                partner_page = f"https://edhrec.com/partners/{name_slug}"
                response = requests.get(partner_page)
                response.raise_for_status()
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                partner_list = soup.find("div", class_=re.compile("cardlist"))
                first_partner = partner_list.find("span", class_=re.compile("Card_name"))
                partner_name = first_partner.get_text()
                print(f"Most popular partner: {partner_name}. Fetching image...")
                payload = {
                    "order": "edhrec",
                    "q": f"{partner_name} is:commander game:paper"
                }
                fetch_partner = requests.get(base_url, params=payload, headers=headers)
                fetch_partner.raise_for_status()
                json_data = fetch_partner.json().get('data')
                partner = json_data[0]
                self.data['partner'] = partner
                main_image = commander.get('image_uris').get('png')
                partner_image = partner.get('image_uris').get('png')
                filepath_cmd = "commander.png"
                filepath_partner = "partner.png"
                main_img_res = requests.get(main_image, stream=True)
                time.sleep(0.1)
                main_img_res.raise_for_status()
                with open(filepath_cmd, 'wb') as out_file:
                    for chunk in main_img_res.iter_content(chunk_size=8192):
                        out_file.write(chunk)
                partner_img_res = requests.get(partner_image, stream=True)
                time.sleep(0.1)
                partner_img_res.raise_for_status()
                with open(filepath_partner, 'wb') as out_file:
                    for chunk in partner_img_res.iter_content(chunk_size=8192):
                        out_file.write(chunk)

                self.original_commander_pixmap = QPixmap(filepath_cmd)
                self.original_partner_pixmap = QPixmap(filepath_partner)
                self.partnerImage.setVisible(True)

            if not self.partnerSearch.isChecked():
                image_uris = commander.get('image_uris')
                if image_uris:
                    image_link = image_uris.get('png')
                    filepath = "commander.png"
                    img_response = requests.get(image_link, stream=True)
                    time.sleep(0.1)
                    img_response.raise_for_status()
                    with open(filepath, 'wb') as out_file:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            out_file.write(chunk)

                    self.original_commander_pixmap = QPixmap(filepath)
                if not image_uris:
                    if "//" in commander.get("name"):
                        faces = commander.get("card_faces")
                        image_front_link = faces[0].get("image_uris", {}).get("png")
                        image_back_link = faces[1].get("image_uris", {}).get("png")
                        self.filepath_front = "commander_front.png"
                        self.filepath_back = "commander_back.png"
                        front_img_response = requests.get(image_front_link, stream=True)
                        time.sleep(0.1)
                        front_img_response.raise_for_status()
                        with open(self.filepath_front, 'wb') as out_file:
                            for chunk in front_img_response.iter_content(chunk_size=8192):
                                out_file.write(chunk)
                        back_img_response = requests.get(image_back_link, stream=True)
                        time.sleep(0.1)
                        back_img_response.raise_for_status()
                        with open(self.filepath_back, 'wb') as out_file:
                            for chunk in back_img_response.iter_content(chunk_size=8192):
                                out_file.write(chunk)
                        self.original_commander_pixmap = QPixmap(self.filepath_front)
                        self.commanderImageFlip.setEnabled(True)
                        self.commanderImageFlip.setVisible(True)
                    else:
                        print("No image URL found for this card.")
                        return

            self.update_commander_image()

        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            self.commanderImage.setText("Failed to load data.")

    def search_random (self):
        # --- MAKE SURE THERE IS NO OLD BACK AND PARTNER LEFT ---#
        if os.path.isfile("commander_back.png"):
            os.remove("commander_back.png")
        if os.path.isfile("partner.png"):
            os.remove("partner.png")


        # --- RESET PARTNER VIEW ---#
        self.partnerImage.setVisible(False)
        self.original_partner_pixmap = None

        # --- RESET FLIP COUNT AND BUTTON ---#
        self.times_clicked_flip = 0
        self.commanderImageFlip.setVisible(False)
        self.commanderImageFlip.setEnabled(False)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "application/json;q=0.9,*/*;q=0.8"
        }

        query = f"{self.searchText.text()}"
        # Add "is:commander" to find only legendary creatures that are legal as commanders.
        if "is:commander" not in query.lower():
            query += " is:commander"
        if "game:paper" not in query.lower():
            query += " game:paper"
        if self.partnerSearch.isChecked():
            query += " o:partner"

        payload = {
            "order": "edhrec",
            "q": query
        }
        base_url = "https://api.scryfall.com/cards/random"

        try:
            response = requests.get(base_url, params=payload, headers=headers)
            time.sleep(0.1)
            response.raise_for_status()  # Raises an error for 4xx/5xx responses
            json_data = response.json()

            if not json_data:
                print("No cards found for this search.")
                self.commanderImage.setText("Commander not found.")
                return

            commander = json_data
            self.data['commander'] = commander

            if self.partnerSearch.isChecked():
                print(f"Looking up most popular partner for {commander.get('name')}...")
                edhrec_link = commander.get("related_uris", {}).get("edhrec")
                if not edhrec_link:
                    print("No EDHRec link found.")
                    return
                response_edhrec = requests.get(edhrec_link)
                response_edhrec.raise_for_status()
                deck_slug = response_edhrec.url
                name_slug = deck_slug.rsplit("/", 1)[-1]
                name_slug = name_slug.replace("?cc=", "")
                partner_page = f"https://edhrec.com/partners/{name_slug}"
                response = requests.get(partner_page)
                response.raise_for_status()
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                partner_list = soup.find("div", class_=re.compile("cardlist"))
                first_partner = partner_list.find("span", class_=re.compile("Card_name"))
                partner_name = first_partner.get_text()
                print(f"Most popular partner: {partner_name}. Fetching image...")
                payload = {
                    "order": "edhrec",
                    "q": f"{partner_name} is:commander game:paper"
                }
                fetch_partner = requests.get("https://api.scryfall.com/cards/search", params=payload, headers=headers)
                fetch_partner.raise_for_status()
                json_data = fetch_partner.json().get('data')
                partner = json_data[0]
                self.data['partner'] = partner
                main_image = commander.get('image_uris').get('png')
                partner_image = partner.get('image_uris').get('png')
                filepath_cmd = "commander.png"
                filepath_partner = "partner.png"
                main_img_res = requests.get(main_image, stream=True)
                time.sleep(0.1)
                main_img_res.raise_for_status()
                with open(filepath_cmd, 'wb') as out_file:
                    for chunk in main_img_res.iter_content(chunk_size=8192):
                        out_file.write(chunk)
                partner_img_res = requests.get(partner_image, stream=True)
                time.sleep(0.1)
                partner_img_res.raise_for_status()
                with open(filepath_partner, 'wb') as out_file:
                    for chunk in partner_img_res.iter_content(chunk_size=8192):
                        out_file.write(chunk)

                self.original_commander_pixmap = QPixmap(filepath_cmd)
                self.original_partner_pixmap = QPixmap(filepath_partner)
                self.partnerImage.setVisible(True)

            if not self.partnerSearch.isChecked():
                image_uris = commander.get('image_uris')
                if image_uris:
                    image_link = image_uris.get('png')
                    filepath = "commander.png"
                    img_response = requests.get(image_link, stream=True)
                    time.sleep(0.1)
                    img_response.raise_for_status()
                    with open(filepath, 'wb') as out_file:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            out_file.write(chunk)

                    self.original_commander_pixmap = QPixmap(filepath)
                if not image_uris:
                    if "//" in commander.get("name"):
                        faces = commander.get("card_faces")
                        image_front_link = faces[0].get("image_uris", {}).get("png")
                        image_back_link = faces[1].get("image_uris", {}).get("png")
                        self.filepath_front = "commander_front.png"
                        self.filepath_back = "commander_back.png"
                        front_img_response = requests.get(image_front_link, stream=True)
                        time.sleep(0.1)
                        front_img_response.raise_for_status()
                        with open(self.filepath_front, 'wb') as out_file:
                            for chunk in front_img_response.iter_content(chunk_size=8192):
                                out_file.write(chunk)
                        back_img_response = requests.get(image_back_link, stream=True)
                        time.sleep(0.1)
                        back_img_response.raise_for_status()
                        with open(self.filepath_back, 'wb') as out_file:
                            for chunk in back_img_response.iter_content(chunk_size=8192):
                                out_file.write(chunk)
                        self.original_commander_pixmap = QPixmap(self.filepath_front)
                        self.commanderImageFlip.setEnabled(True)
                        self.commanderImageFlip.setVisible(True)
                    else:
                        print("No image URL found for this card.")
                        return

            self.update_commander_image()

        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            self.commanderImage.setText("Failed to load data.")

    def update_commander_image(self):
        """Scales the original pixmap and displays it in the label."""
        # Define the minimum height for the image area to ensure it doesn't become too small.
        min_height = int(self.height() * (2 / 3))
        self.commanderImage.setMinimumHeight(min_height)
        self.partnerImage.setMinimumHeight(min_height) # Apply to partner as well for consistent row height

        if not self.original_commander_pixmap:
            return

        # Scale the image to the height of the label, keeping the aspect ratio.
        # Using scaledToHeight is more robust against width constraints from the layout.
        scaled_pixmap = self.original_commander_pixmap.scaledToHeight(
            self.commanderImage.height(),
            Qt.SmoothTransformation
        )
        self.commanderImage.setPixmap(scaled_pixmap)
        self.commanderImage.setAlignment(Qt.AlignCenter)

        if self.original_partner_pixmap:
            scaled_partner_pixmap = self.original_partner_pixmap.scaledToHeight(
                self.partnerImage.height(),
                Qt.SmoothTransformation
            )
            self.partnerImage.setPixmap(scaled_partner_pixmap)
        else:
            # Ensure the partner image label is cleared if no partner is active
            self.partnerImage.clear()

    def flip_image(self):
        if self.times_clicked_flip == 0 or self.times_clicked_flip % 2 == 0:
            self.original_commander_pixmap = QPixmap(self.filepath_back)
        else:
            self.original_commander_pixmap = QPixmap(self.filepath_front)

        self.times_clicked_flip += 1
        self.update_commander_image()

    def resizeEvent(self, event):
        """Called when the window is resized."""
        super().resizeEvent(event)
        self.update_commander_image()

    def fetch_first_decklist_in_budget(self):
        self.errorLabel.setVisible(False)
        if self.partnerSearch.isChecked():
            try:
                commander_edhpage = self.data['commander'].get("related_uris", {}).get("edhrec")
                if not commander_edhpage:
                    self.errorLabel.setText("No EDHRec link found for commander.")
                    self.errorLabel.setVisible(True)
                    return

                comm_response = requests.get(commander_edhpage)
                comm_response.raise_for_status()
                commander_page = comm_response.url

                partner_edhpage = self.data['partner'].get("related_uris", {}).get("edhrec")
                if not partner_edhpage:
                    self.errorLabel.setText("No EDHRec link found for partner.")
                    self.errorLabel.setVisible(True)
                    return
                partner_response = requests.get(partner_edhpage)
                partner_response.raise_for_status()
                partner_page = partner_response.url

                if not commander_page or not partner_page:
                    self.errorLabel.setText("No EDHRec link found for commander or partner.")
                    self.errorLabel.setVisible(True)
                    return
                commander_slug = commander_page.rsplit("/", 1)[-1]
                commander_slug = commander_slug.replace("?cc=", "")
                partner_slug = partner_page.rsplit("/", 1)[-1]
                partner_slug = partner_slug.replace("?cc=", "")
                decks_site = f"https://edhrec.com/decks/{commander_slug}-{partner_slug}"
                partner_response = requests.get(decks_site)
                partner_response.raise_for_status()

                # --- Extract JSON data from the __NEXT_DATA__ script tag ---
                soup = bs4.BeautifulSoup(partner_response.text, 'html.parser')
                next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})

                if not next_data_script:
                    self.errorLabel.setText("Could not find deck data on the page.")
                    self.errorLabel.setVisible(True)
                    return

                data = json.loads(next_data_script.string)
                deck_table = data.get('props', {}).get('pageProps', {}).get('data', {}).get('table', [])

                if not deck_table:
                    self.errorLabel.setText("No decks found in the data.")
                    self.errorLabel.setVisible(True)
                    return

                # --- Filter by budget and search for the first matching deck ---
                try:
                    budget_query = self.price_limit.text().lower()
                    budget_parts = budget_query.split()
                    min_budget = None
                    max_budget = None
                    budget_limit = None
                    for part in budget_parts:
                        part = part.strip()
                        if "-" in part:
                            borders = part.split("-")
                            min_budget = borders[0]
                            max_budget = borders[1]
                        elif ">" in part:
                            min_budget = part.replace(">", "")
                        elif "<" in part:
                            max_budget = part.replace("<", "")
                        else:
                            self.errorLabel.setText(
                                f"Invalid budget format: {part}. Please check the hint below your input.")
                            self.errorLabel.setVisible(True)
                except ValueError:
                    self.errorLabel.setText("Invalid budget. Please enter a number.")
                    self.errorLabel.setVisible(True)
                    return

                first_deck_found = None
                for deck in deck_table:

                    try:
                        if min_budget and max_budget:
                            if float(min_budget) <= deck.get('price', float('inf')) <= float(max_budget):
                                first_deck_found = deck
                                break  # We found the first matching deck
                        elif min_budget and not max_budget:
                            if float(min_budget) <= deck.get('price', float('inf')):
                                first_deck_found = deck
                                break  # We found the first matching deck
                        else:
                            if deck.get('price', float('inf')) <= float(max_budget):
                                first_deck_found = deck
                                break  # We found the first matching deck
                    except (TypeError, ValueError):
                        self.errorLabel.setText(f"Please enter a valid budget.")
                        self.errorLabel.setVisible(True)
                        return

                if first_deck_found:
                    self.deckPriceLabel.setText(f"Decklist found for ${str(first_deck_found.get('price'))}")
                    self.deckPriceLabel.setEnabled(True)
                    deck_url_hash = first_deck_found.get("urlhash")
                    deck_link = f"https://edhrec.com/deckpreview/{deck_url_hash}"
                    print(f"Found deck within budget: {deck_link}")
                    self.data['deck_page'] = deck_link
                    self.copy_list_to_clipboard()
                else:
                    self.errorLabel.setText(f"No decks found in your budget.")
                    self.errorLabel.setVisible(True)

            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                self.errorLabel.setText("Not a valid EDHRec link.")
                self.errorLabel.setVisible(True)
        else:
            if not self.data.get("commander"):
                self.errorLabel.setText("Please search for a commander first.")
                self.errorLabel.setVisible(True)
                return

            edhrec_link = self.data["commander"].get("related_uris", {}).get("edhrec")
            if not edhrec_link:
                print("No EDHRec link found.")
                return

            try:
                # The slug is the last part of the URL, e.g., "kaalia-of-the-vast"
                response_edhrec = requests.get(edhrec_link)
                response_edhrec.raise_for_status()

                deck_slug = response_edhrec.url
                name_slug = deck_slug.rsplit("/", 1)[-1]
                name_slug = name_slug.replace("?cc=", "")
                decks_site = f"https://edhrec.com/decks/{name_slug}"
                response = requests.get(decks_site)
                response.raise_for_status()

                # --- Extract JSON data from the __NEXT_DATA__ script tag ---
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})

                if not next_data_script:
                    self.errorLabel.setText("Could not find deck data on the page.")
                    self.errorLabel.setVisible(True)
                    return

                data = json.loads(next_data_script.string)
                deck_table = data.get('props', {}).get('pageProps', {}).get('data', {}).get('table', [])

                if not deck_table:
                    self.errorLabel.setText("No decks found in the data.")
                    self.errorLabel.setVisible(True)
                    return

                # --- Filter by budget and search for the first matching deck ---
                try:
                    budget_query = self.price_limit.text().lower()
                    budget_parts = budget_query.split()
                    min_budget = None
                    max_budget = None
                    budget_limit = None
                    for part in budget_parts:
                        part = part.strip()
                        if "-" in part:
                            borders = part.split("-")
                            min_budget = borders[0]
                            max_budget = borders[1]
                        elif ">" in part:
                            min_budget = part.replace(">", "")
                        elif "<" in part:
                            max_budget = part.replace("<", "")
                        else:
                            self.errorLabel.setText(f"Invalid budget format: {part}. Please check the hint below your input.")
                            self.errorLabel.setVisible(True)
                except ValueError:
                    self.errorLabel.setText("Invalid budget. Please enter a number.")
                    self.errorLabel.setVisible(True)
                    return

                first_deck_found = None
                for deck in deck_table:
                    try:
                        if min_budget and max_budget:
                            if float(min_budget) <= deck.get('price', float('inf')) <= float(max_budget):
                                first_deck_found = deck
                                break  # We found the first matching deck
                        elif min_budget and not max_budget:
                            if float(min_budget) <= deck.get('price', float('inf')):
                                first_deck_found = deck
                                break  # We found the first matching deck
                        else:
                            if deck.get('price', float('inf')) <= float(max_budget):
                                first_deck_found = deck
                                break  # We found the first matching deck
                    except (TypeError, ValueError):
                        self.errorLabel.setText(f"Please enter a valid budget.")
                        self.errorLabel.setVisible(True)
                        return

                if first_deck_found:
                    self.deckPriceLabel.setText(f"Decklist found for ${str(first_deck_found.get('price'))}")
                    self.deckPriceLabel.setEnabled(True)
                    deck_url_hash = first_deck_found.get("urlhash")
                    deck_link = f"https://edhrec.com/deckpreview/{deck_url_hash}"
                    print(f"Found deck within budget: {deck_link}")
                    self.data['deck_page'] = deck_link
                    self.copy_list_to_clipboard()
                else:
                    self.errorLabel.setText(f"No decks found in your budget.")
                    self.errorLabel.setVisible(True)


            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                self.errorLabel.setText("Not a valid EDHRec link.")
                self.errorLabel.setVisible(True)

    def copy_list_to_clipboard(self):

        self.errorLabel.setVisible(False)
        deck_page = self.data.get("deck_page", "")

        if not deck_page:
            self.errorLabel.setText("Deck page not accessible.")
            self.errorLabel.setVisible(True)
            return

        try:
            response = requests.get(deck_page)
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            data = json.loads(next_data_script.string)
            deck_link = data.get("props", {}).get("pageProps", {}).get("data", {}).get("url", "")

            match deck_link:
                case _ if "moxfield.com" in deck_link or "archidekt.com" in deck_link:
                    # --- Selenium-based approach ---
                    self.get_Decklist.setEnabled(False)
                    site_name = "Moxfield" if "moxfield" in deck_link else "Archidekt"
                    self.errorLabel.setStyleSheet(f"background-color: lightgrey; color: black;")
                    self.errorLabel.setText(f"Fetching from {site_name}...")
                    self.errorLabel.setVisible(True)
                    self.thread = QThread()
                    self.worker = DecklistScraperWorker(deck_link)
                    self.worker.moveToThread(self.thread)
                    self.thread.started.connect(self.worker.run)
                    self.worker.finished.connect(self.on_selenium_finished)
                    self.thread.start()
                case _:
                    self.errorLabel.setText(f"Unsupported site for scraping: {deck_link}")
                    self.errorLabel.setVisible(True)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            self.errorLabel.setText("Not a valid deck link.")
            self.errorLabel.setVisible(True)

    def show_syntax_guide(self):
        webbrowser.open("https://scryfall.com/docs/syntax")

    def on_selenium_finished(self, decklist):
        """Handles the result from the Selenium worker thread."""
        self.errorLabel.setVisible(False)

        if "Error" in decklist:
            self.errorLabel.setText(decklist)
            self.errorLabel.setVisible(True)
        else:
            pyperclip.copy(decklist)
            self.errorLabel.setText("Decklist copied to clipboard!")
            self.errorLabel.setVisible(True)

        self.get_Decklist.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def closeEvent(self, a0):
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if os.path.isfile("commander.png"):
                os.remove("commander.png")
            if os.path.isfile("commander_back.png"):
                os.remove("commander_back.png")
            if os.path.isfile("commander_front.png"):
                os.remove("commander_front.png")
            if os.path.isfile("partner.png"):
                os.remove("partner.png")
            a0.accept()
        else:
            a0.ignore()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
