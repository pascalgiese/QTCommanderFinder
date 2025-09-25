import os
import re
import sys
import json
import urllib.request
import webbrowser
import pyperclip
import requests
from PyQt5.QtCore import Qt, QThread
import bs4
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, \
    QLineEdit, \
    QPushButton, QMessageBox, QGridLayout
from PyQt5.QtGui import QPixmap, QIcon

from src.config.constants import (
    EDHREC_TAGS, COMMANDER_IMG_PATH, COMMANDER_FRONT_IMG_PATH, COMMANDER_BACK_IMG_PATH, PARTNER_IMG_PATH,
    SCRYFALL_API_CARD_SEARCH_URL, SCRYFALL_API_CARD_RANDOM_URL, HTTP_HEADERS, EDHREC_PARTNERS_URL_TPL,
    EDHREC_DECKS_URL_TPL, EDHREC_DECK_PREVIEW_URL_TPL, SCRYFALL_SYNTAX_GUIDE_URL, DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH
)
from src.scraping.scraper_worker import DecklistScraperWorker
from src.ui.completer import MultiTagCompleter
from src.utils.deck_filter import filter_decks
from src.utils.file_helpers import resource_path


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

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Filter by tags (e.g. counters, budget)")

        # --- TAG COMPLETION ---
        completer = MultiTagCompleter(EDHREC_TAGS, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.tags_input.setCompleter(completer)

        self.budget_hint = QLabel(
            "Budget search allows minus-separated ranges, min values with >, and max values with <")
        self.partnerSearch = QCheckBox("Search Partner Combo")
        self.helpButton = QPushButton("Syntax Guide")
        self.helpButton.clicked.connect(self.show_syntax_guide)

        #--- EXTENDED SEARCH CONTAINER ---#
        self.extendedSearchLayout = QGridLayout()
        self.extendedSearchLayout.setContentsMargins(0,0,0,0)
        self.extendedSearchLayout.setSpacing(5)
        self.extendedSearchLayout.addWidget(self.price_limit, 0, 0)
        self.extendedSearchLayout.addWidget(self.tags_input, 0, 1)
        self.extendedSearchLayout.addWidget(self.partnerSearch, 0, 2)
        self.extendedSearchLayout.addWidget(self.helpButton, 0, 3)
        self.extendedSearchLayout.addWidget(self.budget_hint, 1, 0, 1, 4, Qt.AlignTop)

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

    def _cleanup_temp_files(self):
        """Removes temporary image files."""
        for f in [COMMANDER_BACK_IMG_PATH, PARTNER_IMG_PATH, COMMANDER_IMG_PATH, COMMANDER_FRONT_IMG_PATH]:
            if os.path.isfile(f):
                os.remove(f)

    def _reset_ui_state(self):
        """Resets UI elements to their initial state for a new search."""
        self._cleanup_temp_files()

        # Reset partner view
        self.partnerImage.setVisible(False)
        self.original_partner_pixmap = None

        # Reset flip count and button
        self.times_clicked_flip = 0
        self.commanderImageFlip.setVisible(False)
        self.commanderImageFlip.setEnabled(False)

        # Reset data cache for images
        self.filepath_front = None
        self.filepath_back = None
        self.original_commander_pixmap = None

    def _set_status(self, message, is_error=False):
        """Updates the status label."""
        if is_error:
            self.errorLabel.setStyleSheet("background-color: red; color: black;")
        else:
            self.errorLabel.setStyleSheet("background-color: lightgrey; color: black;")
        self.errorLabel.setText(message)
        self.errorLabel.setVisible(True)
        QApplication.processEvents()

    def _build_scryfall_query(self):
        """Constructs the Scryfall query string from the UI."""
        query = self.searchText.text().strip()
        if "is:commander" not in query.lower():
            query += " is:commander"
        if "game:paper" not in query.lower():
            query += " game:paper"
        if self.partnerSearch.isChecked() and "o:partner" not in query.lower():
            query += " o:partner"
        return query

    def _download_and_display_card_image(self, card_data):
        """
        Downloads the image for a given card (including double-faced cards)
        and sets it up for display.
        """
        image_uris = card_data.get('image_uris')
        if image_uris:
            image_link = image_uris.get('png')
            urllib.request.urlretrieve(image_link, COMMANDER_IMG_PATH)
            time.sleep(0.1)
            self.original_commander_pixmap = QPixmap(COMMANDER_IMG_PATH)
        elif "card_faces" in card_data:
            faces = card_data.get("card_faces")
            image_front_link = faces[0].get("image_uris", {}).get("png")
            image_back_link = faces[1].get("image_uris", {}).get("png")
            self.filepath_front = COMMANDER_FRONT_IMG_PATH
            self.filepath_back = COMMANDER_BACK_IMG_PATH
            urllib.request.urlretrieve(image_front_link, self.filepath_front)
            time.sleep(0.1)
            urllib.request.urlretrieve(image_back_link, self.filepath_back)
            time.sleep(0.1)
            self.original_commander_pixmap = QPixmap(self.filepath_front)
            self.commanderImageFlip.setEnabled(True)
            self.commanderImageFlip.setVisible(True)
        else:
            self._set_status(f"No image found for {card_data.get('name')}.", is_error=True)
            return False
        return True

    def search(self):
        self._reset_ui_state()
        self._set_status("Looking for specified card...")

        query = self._build_scryfall_query()
        payload = {"order": "edhrec", "q": query}

        try:
            response = requests.get(SCRYFALL_API_CARD_SEARCH_URL, params=payload, headers=HTTP_HEADERS)
            time.sleep(0.1)
            response.raise_for_status()
            json_data = response.json().get('data')

            if not json_data:
                self._set_status("Commander not found.", is_error=True)
                return

            commander = json_data[0]
            self.data['commander'] = commander

            if self.partnerSearch.isChecked():
                if not self._handle_partner_search(commander):
                    return
            else:
                if not self._download_and_display_card_image(commander):
                    return

            self.update_commander_image()
            self._set_status("Commander found.")

        except requests.exceptions.RequestException as e:
            self._set_status(f"API request error: {e}", is_error=True)
            self.commanderImage.setText("Failed to load data.")

    def search_random(self):
        self._reset_ui_state()
        self._set_status("Finding random commander...")

        query = self._build_scryfall_query()
        payload = {"q": query}

        try:
            response = requests.get(SCRYFALL_API_CARD_RANDOM_URL, params=payload, headers=HTTP_HEADERS)
            time.sleep(0.1)
            response.raise_for_status()
            commander = response.json()

            if not commander:
                self._set_status("Commander not found.", is_error=True)
                return

            self.data['commander'] = commander

            if self.partnerSearch.isChecked():
                if not self._handle_partner_search(commander):
                    return
            else:
                if not self._download_and_display_card_image(commander):
                    return

            self.update_commander_image()
            self._set_status("Commander found.")

        except requests.exceptions.RequestException as e:
            self._set_status(f"API request error: {e}", is_error=True)
            self.commanderImage.setText("Failed to load data.")

    def _handle_partner_search(self, commander):
        self._set_status(f"Looking up most popular partner for {commander.get('name')}...")

        edhrec_link = commander.get("related_uris", {}).get("edhrec")
        if not edhrec_link:
            self._set_status(f"No EDHRec link found for {commander.get('name')}.", is_error=True)
            return False

        try:
            response_edhrec = requests.get(edhrec_link)
            response_edhrec.raise_for_status()
            deck_slug = response_edhrec.url.rsplit("/", 1)[-1].replace("?cc=", "")

            partner_page_url = EDHREC_PARTNERS_URL_TPL.format(slug=deck_slug)
            response = requests.get(partner_page_url)
            response.raise_for_status()

            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            partner_list = soup.find("div", class_=re.compile("cardlist"))
            if not partner_list:
                self._set_status(f"Could not find partner list for {commander.get('name')}.", is_error=True)
                return False

            first_partner_span = partner_list.find("span", class_=re.compile("Card_name"))
            if not first_partner_span:
                self._set_status(f"Could not find a partner for {commander.get('name')}.", is_error=True)
                return False

            partner_name = first_partner_span.get_text()
            self._set_status(f"Most popular partner: {partner_name}. Fetching image...")

            # Fetch partner card data from Scryfall
            payload = {"order": "edhrec", "q": f'"{partner_name}" is:commander game:paper'}
            fetch_partner_resp = requests.get(SCRYFALL_API_CARD_SEARCH_URL, params=payload, headers=HTTP_HEADERS)
            fetch_partner_resp.raise_for_status()
            json_data = fetch_partner_resp.json().get('data')
            if not json_data:
                self._set_status(f"Could not find card data for partner: {partner_name}", is_error=True)
                return False

            partner = json_data[0]
            self.data['partner'] = partner

            # Download commander image (including double-faced)
            if not self._download_and_display_card_image(commander):
                return False # Cannot proceed without commander image

            # Download partner image
            p_image_uris = partner.get('image_uris', {})
            if p_image_uris.get('png'):
                 urllib.request.urlretrieve(p_image_uris.get('png'), PARTNER_IMG_PATH)
                 self.original_partner_pixmap = QPixmap(PARTNER_IMG_PATH)
                 self.partnerImage.setVisible(True)
            else:
                # Partners are not typically double-faced, but good to be safe
                self._set_status(f"No image found for partner {partner.get('name')}.", is_error=True)
                # We can proceed without the partner image, so we don't return False

            return True

        except requests.exceptions.RequestException as e:
            self._set_status(f"API request error during partner search: {e}", is_error=True)
            return False
        except Exception as e:
            self._set_status(f"An error occurred during partner search: {e}", is_error=True)
            return False

    def update_commander_image(self):
        """Scales the original pixmap and displays it in the label."""
        min_height = int(self.height() * (2 / 3))
        self.commanderImage.setMinimumHeight(min_height)
        self.partnerImage.setMinimumHeight(min_height)

        if self.original_commander_pixmap:
            scaled_pixmap = self.original_commander_pixmap.scaledToHeight(
                self.commanderImage.height(),
                Qt.SmoothTransformation
            )
            self.commanderImage.setPixmap(scaled_pixmap)
        else:
            self.commanderImage.clear()

        if self.original_partner_pixmap:
            scaled_partner_pixmap = self.original_partner_pixmap.scaledToHeight(
                self.partnerImage.height(),
                Qt.SmoothTransformation
            )
            self.partnerImage.setPixmap(scaled_partner_pixmap)
        else:
            self.partnerImage.clear()

    def flip_image(self):
        if self.times_clicked_flip % 2 == 0:
            self.original_commander_pixmap = QPixmap(self.filepath_back)
        else:
            self.original_commander_pixmap = QPixmap(self.filepath_front)

        self.times_clicked_flip += 1
        self.update_commander_image()

    def resizeEvent(self, event):
        """Called when the window is resized."""
        super().resizeEvent(event)
        self.update_commander_image()

    def _get_edhrec_deck_table(self):
        """Fetches and parses the deck table from EDHRec for a commander or partner pair."""
        if self.partnerSearch.isChecked():
            if 'commander' not in self.data or 'partner' not in self.data:
                self._set_status("Please search for a commander and partner first.", is_error=True)
                return None

            commander_slug_part = self.data['commander'].get("name", "").lower().replace(" ", "-").replace(",", "")
            partner_slug_part = self.data['partner'].get("name", "").lower().replace(" ", "-").replace(",", "")
            # This is a guess, EDHRec URL slugs can be complex. A more robust way is needed if this fails.
            # Let's try to get it from the edhrec page url itself
            comm_edhrec_url = self.data['commander'].get("related_uris", {}).get("edhrec")
            part_edhrec_url = self.data['partner'].get("related_uris", {}).get("edhrec")
            if not comm_edhrec_url or not part_edhrec_url:
                self._set_status("EDHRec links missing for commander or partner.", is_error=True)
                return None

            comm_slug = requests.get(comm_edhrec_url).url.rsplit("/", 1)[-1].replace("?cc=", "")
            part_slug = requests.get(part_edhrec_url).url.rsplit("/", 1)[-1].replace("?cc=", "")

            decks_site_url = EDHREC_DECKS_URL_TPL.format(slug=f"{comm_slug}-{part_slug}")
        else:
            if "commander" not in self.data:
                self._set_status("Please search for a commander first.", is_error=True)
                return None

            edhrec_link = self.data["commander"].get("related_uris", {}).get("edhrec")
            if not edhrec_link:
                self._set_status("No EDHRec link found for commander.", is_error=True)
                return None

            # Follow redirect to get the correct slug
            response_edhrec = requests.get(edhrec_link)
            response_edhrec.raise_for_status()
            name_slug = response_edhrec.url.rsplit("/", 1)[-1].replace("?cc=", "")
            decks_site_url = EDHREC_DECKS_URL_TPL.format(slug=name_slug)

        # Fetch the decks page and parse __NEXT_DATA__
        response = requests.get(decks_site_url)
        response.raise_for_status()

        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        if not next_data_script:
            self._set_status("Could not find deck data on the page.", is_error=True)
            return None

        data = json.loads(next_data_script.string)
        deck_table = data.get('props', {}).get('pageProps', {}).get('data', {}).get('table', [])
        if not deck_table:
            self._set_status("No decks found in the data.", is_error=True)
            return None

        return deck_table

    def fetch_first_decklist_in_budget(self):
        self.errorLabel.setVisible(False)

        try:
            deck_table = self._get_edhrec_deck_table()
            if deck_table is None:
                return # Error was already set by the helper method

            budget_query = self.price_limit.text().strip()
            tags_query = self.tags_input.text().strip().lower()

            first_deck_found = filter_decks(deck_table, budget_query, tags_query)

            if first_deck_found:
                price = first_deck_found.get('price')
                self.deckPriceLabel.setText(f"Decklist found for ${price}")
                self.deckPriceLabel.setEnabled(True)

                deck_url_hash = first_deck_found.get("urlhash")
                deck_preview_link = EDHREC_DECK_PREVIEW_URL_TPL.format(hash=deck_url_hash)

                self._set_status(f"Found deck for ${price}. Preparing to fetch...")
                print(f"Found deck within budget: {deck_preview_link}")

                self.data['deck_page'] = deck_preview_link
                self.start_decklist_scraping()
            else:
                self._set_status("No decks found matching your filters.", is_error=True)

        except (ValueError, IndexError):
            self._set_status("Invalid budget format. Use numbers, '>', '<', or '-'.", is_error=True)
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            self._set_status(f"Network error fetching deck data: {e}", is_error=True)
        except Exception as e:
            print(f"Unexpected error in fetch_first_decklist_in_budget: {e}")
            self._set_status(f"An unexpected error occurred: {e}", is_error=True)

    def start_decklist_scraping(self):
        self.errorLabel.setVisible(False)
        deck_page = self.data.get("deck_page", "")

        if not deck_page:
            self._set_status("Deck page not accessible.", is_error=True)
            return

        try:
            response = requests.get(deck_page)
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            data = json.loads(next_data_script.string)
            deck_link = data.get("props", {}).get("pageProps", {}).get("data", {}).get("url", "")

            if "moxfield.com" in deck_link or "archidekt.com" in deck_link:
                self.get_Decklist.setEnabled(False)
                site_name = "Moxfield" if "moxfield" in deck_link else "Archidekt"
                self._set_status(f"Fetching from {site_name}...")

                self.thread = QThread()
                self.worker = DecklistScraperWorker(deck_link)
                self.worker.moveToThread(self.thread)
                self.thread.started.connect(self.worker.run)
                self.worker.finished.connect(self.on_selenium_finished)
                self.thread.start()
            else:
                self._set_status(f"Unsupported site for scraping: {deck_link}", is_error=True)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            self._set_status("Not a valid deck link.", is_error=True)

    def show_syntax_guide(self):
        webbrowser.open(SCRYFALL_SYNTAX_GUIDE_URL)

    def on_selenium_finished(self, decklist):
        """Handles the result from the Selenium worker thread."""
        self.errorLabel.setVisible(False)

        if "Error" in decklist:
            self._set_status(decklist, is_error=True)
        else:
            pyperclip.copy(decklist)
            self._set_status("Decklist copied to clipboard!")

        self.get_Decklist.setEnabled(True)
        if self.thread:
            self.thread.quit()
            self.thread.wait()

    def closeEvent(self, a0):
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self._cleanup_temp_files()
            # Clean up debug screenshots
            for f in [DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH, "debug_screenshot_moxfield.png", "debug_screenshot_archidekt.png"]:
                 if os.path.isfile(f):
                    os.remove(f)
            a0.accept()
        else:
            a0.ignore()