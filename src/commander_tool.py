import sys
import json

import pyperclip
import requests
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
import bs4
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QLineEdit, \
    QPushButton, QLayout
from PyQt5.QtGui import QPalette, QColor, QPixmap
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_stealth import stealth


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

        # Apply selenium-stealth to bypass bot detection like Cloudflare.
        # Dies muss NACH der Initialisierung des Treibers, aber VOR dem ersten .get() Aufruf geschehen.
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

        except TimeoutException as e:
            error_message = f"Error: Timed out on {self.site.capitalize()}. Check selectors or page load."
            print(f"--- SELENIUM DEBUG: TIMEOUT ---")
            print(f"Error message: {e}")
            driver.save_screenshot(f"debug_screenshot_{self.site}.png")
            print(f"Screenshot saved to debug_screenshot_{self.site}.png")
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
        # Wir warten kurz, um sicherzustellen, dass die Seite und das __NEXT_DATA__-Skript vollständig geladen sind.
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

        # Hole den HTML-Quellcode der Seite
        soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})

        if not next_data_script:
            self.finished.emit("Error: Could not find __NEXT_DATA__ script tag on Archidekt.")
            return

        data = json.loads(next_data_script.string)

        # Navigiere durch die JSON-Struktur, um zur Kartenliste zu gelangen
        # Korrekter Pfad und korrekte Datenstruktur (dict of dicts)
        card_map = data.get('props', {}).get('pageProps', {}).get('redux', {}).get('deck', {}).get("cardMap", {})

        if not card_map:
            self.finished.emit("Error: Could not find card list (cardMap) in Archidekt's page data.")
            return

        # Formatiere die Deckliste
        decklist_lines = []
        # Da card_map ein Dictionary ist, iterieren wir über seine Werte.
        card_list = list(card_map.values())

        # Sortiere die Karten nach Namen für eine konsistente Ausgabe
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

        #--- WINDOW SETTINGS ---#
        self.setWindowTitle("QTCommanderFinder")
        self.setMinimumSize(400,600)

        # --- THREADING ---#
        self.thread = None
        self.worker = None

        # --- COLOR CHECKBOXES ---#
        # self.colorsLabel = QLabel("Colors:")
        # self.whiteManaButton = QCheckBox()
        # self.whiteManaButton.setText("W")
        # self.blueManaButton = QCheckBox()
        # self.blueManaButton.setText("U")
        # self.blackManaButton = QCheckBox()
        # self.blackManaButton.setText("B")
        # self.redManaButton = QCheckBox()
        # self.redManaButton.setText("R")
        # self.greenManaButton = QCheckBox()
        # self.greenManaButton.setText("G")
        # self.colorlessManaButton = QCheckBox()
        # self.colorlessManaButton.setText("C")

        # --- TEXT SEARCH BAR ---#
        self.searchText = QLineEdit()
        self.searchText.setPlaceholderText("Search a commander...")

        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.search)

        # --- SEARCHBAR LAYOUT ---#
        self.searchMenuLayout = QHBoxLayout()
        # self.searchMenuLayout.addWidget(self.colorsLabel)
        # self.searchMenuLayout.addWidget(self.whiteManaButton)
        # self.searchMenuLayout.addWidget(self.blueManaButton)
        # self.searchMenuLayout.addWidget(self.blackManaButton)
        # self.searchMenuLayout.addWidget(self.redManaButton)
        # self.searchMenuLayout.addWidget(self.greenManaButton)
        # self.searchMenuLayout.addWidget(self.colorlessManaButton)
        self.searchMenuLayout.addWidget(self.searchText)
        self.searchMenuLayout.addWidget(self.searchButton)

        #--- EXTENDED SEARCH BAR ---#
        self.price_limit = QLineEdit()
        self.price_limit.setPlaceholderText("Enter your maximum budget...")

        #--- EXTENDED SEARCH CONTAINER ---#
        self.extendedSearchLayout = QHBoxLayout()
        self.extendedSearchLayout.addWidget(self.price_limit)

        #--- IMAGE CONTAINER ---#
        self.commanderImage = QLabel(self)
        self.commanderImage.setAlignment(Qt.AlignCenter)

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
        self.actionLayout.setSizeConstraint(QLayout.SetFixedSize)

        #--- ERROR BOX ---#
        self.errorLabel = QLabel()
        self.errorLabel.setEnabled(False)
        self.errorLabel.setAlignment(Qt.AlignCenter)

        #--- ERROR BOX CONTAINER ---#
        self.errorLayout = QHBoxLayout()
        self.errorLayout.addWidget(self.errorLabel)
        self.errorLayout.setSizeConstraint(QLayout.SetFixedSize)

        #--- FINAL LAYOUT ---#
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.searchMenuLayout)
        self.layout.addLayout(self.extendedSearchLayout)
        self.layout.addWidget(self.commanderImage)
        self.layout.addLayout(self.actionLayout)
        self.layout.addLayout(self.errorLayout)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

    def search (self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "application/json;q=0.9,*/*;q=0.8"
        }

        # colors = ""
        # for button in [self.whiteManaButton, self.blueManaButton, self.blackManaButton, self.redManaButton, self.greenManaButton, self.colorlessManaButton]:
        #     if button.isChecked():
        #         colors += button.text()

        query = f"{self.searchText.text()}"
        # Füge "is:commander" hinzu, um nur legendäre Kreaturen zu finden, die als Commander legal sind.
        if "is:commander" not in query.lower():
            query += " is:commander"

        payload = {
            "order": "edhrec",
            "q": query
        }
        base_url = "https://api.scryfall.com/cards/search"

        try:
            response = requests.get(base_url, params=payload, headers=headers)
            response.raise_for_status()  # Löst einen Fehler bei 4xx/5xx-Antworten aus
            json_data = response.json().get('data')

            if not json_data:
                print("Keine Karten für diese Suche gefunden.")
                self.commanderImage.setText("Commander not found.")
                return

            commander = json_data[0]
            self.data['commander'] = commander
            image_uris = commander.get('image_uris')
            if not image_uris:
                print("Keine Bild-URL für diese Karte gefunden.")
                return

            image_link = image_uris.get('png')
            filepath = "commander.png"
            img_response = requests.get(image_link, stream=True)
            img_response.raise_for_status()
            with open(filepath, 'wb') as out_file:
                for chunk in img_response.iter_content(chunk_size=8192):
                    out_file.write(chunk)

            self.original_commander_pixmap = QPixmap(filepath)
            self.update_commander_image()

        except requests.exceptions.RequestException as e:
            print(f"Fehler bei der API-Anfrage: {e}")
            self.commanderImage.setText("Failed to load data.")

    def update_commander_image(self):
        """Skaliert das Original-Pixmap und zeigt es im Label an."""
        # Definiere die Mindesthöhe des Bild-Labels als 2/3 der Fensterhöhe.
        # Dies stellt sicher, dass der Bereich für das Bild nicht zu klein wird.
        min_height = int(self.height() * (2 / 3))
        self.commanderImage.setMinimumHeight(min_height)

        if not self.original_commander_pixmap:
            return

        # Skaliere das Bild auf die Größe des Labels, behalte das Seitenverhältnis bei.
        # Die Größe des Labels wird durch das Layout bestimmt, respektiert aber die Mindesthöhe.
        scaled_pixmap = self.original_commander_pixmap.scaled(
            self.commanderImage.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.commanderImage.setPixmap(scaled_pixmap)
        self.commanderImage.setAlignment(Qt.AlignCenter)

    def resizeEvent(self, event):
        """Wird aufgerufen, wenn das Fenster seine Größe ändert."""
        super().resizeEvent(event)
        self.update_commander_image()

    def fetch_first_decklist_in_budget(self):
        if not self.data.get("commander"):
            self.errorLabel.setText("Please search for a commander first.")
            return

        edhrec_link = self.data["commander"].get("related_uris", {}).get("edhrec")
        if not edhrec_link:
            print("Kein EDHRec Link hinterlegt.")
            return

        try:
            # Der Slug ist der letzte Teil der URL, z.B. "kaalia-of-the-vast"
            response_edhrec = requests.get(edhrec_link)
            response_edhrec.raise_for_status()

            deck_slug = response_edhrec.url
            name_slug = deck_slug.rsplit("/", 1)[-1]
            name_slug = name_slug.replace("?cc=", "")
            decks_site = f"https://edhrec.com/decks/{name_slug}"
            response = requests.get(decks_site)
            response.raise_for_status()

            # --- JSON-Daten aus dem __NEXT_DATA__ Skript-Tag extrahieren ---
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})

            if not next_data_script:
                self.errorLabel.setText("Could not find deck data on the page.")
                return

            data = json.loads(next_data_script.string)
            deck_table = data.get('props', {}).get('pageProps', {}).get('data', {}).get('table', [])

            if not deck_table:
                self.errorLabel.setText("No decks found in the data.")
                return

            # --- Budget-Filterung und Suche nach dem ersten passenden Deck ---
            try:
                budget_limit = float(self.price_limit.text()) if self.price_limit.text() else float('inf')
            except ValueError:
                self.errorLabel.setText("Invalid budget. Please enter a number.")
                return

            first_deck_found = None
            for deck in deck_table:
                if deck.get('price', float('inf')) <= budget_limit:
                    first_deck_found = deck
                    break  # Wir haben das erste passende Deck gefunden

            if first_deck_found:
                self.deckPriceLabel.setText(f"Deckliste gefunden für ${str(first_deck_found.get("price"))}")
                self.deckPriceLabel.setEnabled(True)
                deck_url_hash = first_deck_found.get("urlhash")
                deck_link = f"https://edhrec.com/deckpreview/{deck_url_hash}"
                print(f"Found deck within budget: {deck_link}")
                self.data['deck_page'] = deck_link
                self.copy_list_to_clipboard()
            else:
                self.errorLabel.setText(f"No decks found under ${budget_limit:.2f}")


        except requests.exceptions.RequestException as e:
            print(f"Fehler bei der Anfrage: {e}")
            self.errorLabel.setText("Kein valider EDHRec Link.")

    def copy_list_to_clipboard(self):
        deck_page = self.data.get("deck_page", "")

        if not deck_page:
            self.errorLabel.setText("Deck page not accessible.")
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
                    # --- Selenium-basierter Ansatz ---
                    self.get_Decklist.setEnabled(False)
                    site_name = "Moxfield" if "moxfield" in deck_link else "Archidekt"
                    self.errorLabel.setText(f"Fetching from {site_name}...")
                    self.thread = QThread()
                    self.worker = DecklistScraperWorker(deck_link)
                    self.worker.moveToThread(self.thread)
                    self.thread.started.connect(self.worker.run)
                    self.worker.finished.connect(self.on_selenium_finished)
                    self.thread.start()
                case _:
                    self.errorLabel.setText(f"Unsupported site for scraping: {deck_link}")

        except requests.exceptions.RequestException as e:
            print(f"Fehler bei der Anfrage: {e}")
            self.errorLabel.setText("Kein valider Deck Link.")

    def on_selenium_finished(self, decklist):
        """Handles the result from the Selenium worker thread."""
        if "Error" in decklist:
            self.errorLabel.setText(decklist)
        else:
            pyperclip.copy(decklist)
            self.errorLabel.setText("Decklist copied to clipboard!")

        self.get_Decklist.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
