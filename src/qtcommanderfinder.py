import os
import re
import sys
import json
import urllib.request
import webbrowser
import pyperclip
import requests
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
import bs4
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, \
    QLineEdit, \
    QPushButton, QLayout, QMessageBox, QGridLayout
from PyQt5.QtGui import QPalette, QColor, QPixmap, QIcon
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_stealth import stealth
from PyQt5.QtWidgets import QCompleter

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In development, use the script's directory
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

EDHREC_TAGS = [
    "+1/+1 Counters", "Ad Nauseam", "Advisors", "Adventure", "Adventures", "Affinity", "Aggro", "Aikido",
    "Allies", "Amass", "Angels", "Anthems", "Apes", "Arcane", "Archers", "Aristocrats", "Artificers",
    "Artifacts", "Assassins", "Astartes", "Atogs", "Attack Triggers", "Attractions", "Auras", "Avatars",
    "Banding", "Bant", "Barbarians", "Bears", "Beasts", "Big Mana", "Birds", "Birthing Pod",
    "Blink", "Blood", "Blue Moon", "Boros", "Bounce", "Budget", "Burn", "Cantrips", "Card Draw",
    "Cascade", "Cats", "Caves", "cEDH", "Cephalids", "Chaos", "Charge Counters", "Cheerios", "Clerics",
    "Clones", "Clues", "Coin Flip", "Color Hack", "Colorless", "Combo", "Commander Matters", "Companions",
    "Conspicuous", "Constructs", "Control", "Convoke", "Counters", "Crabs", "Craft", "Creatureless",
    "Crime", "Curses", "Cybermen", "Cycling", "Daleks", "Dandan", "Day / Night", "Deathtouch", "Defenders",
    "Delirium", "Delver", "Demons", "Descend", "Deserts", "Detectives", "Devils", "Devotion", "Die Roll",
    "Dimir", "Dinosaurs", "Discard", "Discover", "Dogs", "Dolmen Gate", "Donate", "Dredge", "Drakes",
    "Dragon's Approach", "Dragons", "Druids", "Dune-Brood", "Dungeon", "Dwarves", "Eggs", "Elders",
    "Eldrazi", "Elementals", "Elephants", "Elves", "Enchantress", "Energy", "Enrage", "Equipment", "Esper",
    "ETB", "Evoke", "Exalted", "Exile", "Experience Counters", "Exploit", "Explore", "Extra Combats",
    "Extra Turns", "Faeries", "Fight", "Finisher", "Five-Color", "Flash", "Flashback",
    "Fling", "Flying", "Food", "Forced Combat", "Foretell", "Foxes", "Freerunning", "Frogs", "Fungi",
    "Gaea's Cradle", "Giants", "Glint-Eye", "Gnomes", "Goblins", "Gods", "Golems", "Golgari", "Good Stuff",
    "Gorgons", "Graveyard", "Griffins", "Grixis", "Group Hug", "Group Slug", "Gruul", "Guildgates",
    "Gyruda Companion", "Halflings", "Hand Size", "Hare Apparent", "Haste", "Hatebears", "Hellbent",
    "Heroic", "High Power", "Hippos", "Historic", "Horrors", "Horses", "Humans", "Hydras", "Illusions",
    "Impulse Draw", "Improvise", "Infect", "Ink-Treader", "Insects", "Izzet", "Jegantha Companion",
    "Jeskai", "Jund", "Kaheera Companion", "Keruga Companion", "Keywords", "Kicker", "Kindred", "Kithkin",
    "Knights", "Kor", "Land Animation", "Land Destruction", "Landfall", "Lands Matter", "Landwalk",
    "Legends", "Lhurgoyfs", "Life Exchange", "Lifedrain", "Lifegain", "Lizards", "Lurrus Companion",
    "Lure", "Madness", "Mardu", "Mercenaries", "Merfolk", "Mice", "Midrange", "Mill", "Minions",
    "Minotaurs", "Modular", "Monarch", "Monkeys", "Monks", "Mono-Black", "Mono-Blue", "Mono-Green",
    "Mono-Red", "Mono-White", "Morph", "Mount", "Multicolor Matters", "Mutants", "Mutate", "Myr",
    "Myriad", "Naya", "Necrons", "Nightmares", "Ninjas", "Ninjutsu", "Obosh Companion", "Offspring",
    "Ogres", "Oil Counters", "Old School", "Oozes", "Orcs", "Orzhov", "Otters", "Outlaws", "Paradox",
    "Party", "Persistent Petitioners", "Phasing", "Phoenixes", "Phyrexians", "Pillow Fort", "Pingers",
    "Pirates", "Planeswalkers", "Plants", "Politics", "Polymorph", "Populate", "Power", "Praetors",
    "Primal Surge", "Prison", "Proliferate", "Prowess", "Rabbits", "Raccoons", "Rad Counters",
    "Rakdos", "Ramp", "Rat Colony", "Rats", "Reach", "Reanimator", "Rebels", "Relentless Rats", "Robots",
    "Rock", "Rogues", "Rooms", "Saboteurs", "Sacrifice", "Sagas", "Samurai", "Saprolings", "Satyrs",
    "Scarecrows", "Scry", "Sea Creatures", "Selesnya", "Self-Damage", "Self-Discard", "Self-Mill",
    "Servos", "Shades", "Shadowborn Apostles", "Shamans", "Shapeshifters", "Sharks", "Shrines", "Simic",
    "Skeletons", "Skulk", "Slivers", "Slime Against Humanity", "Snakes", "Sneak Attack", "Snow",
    "Soldiers", "Specters", "Spell Copy", "Spellslinger", "Sphinxes", "Spiders", "Spirits",
    "Spore Counters", "Squad", "Squirrels", "Stax", "Stickers", "Stompy", "Stoneblade", "Storm",
    "Sultai", "Sunforger", "Superfriends", "Surveil", "Suspend", "Tap / Untap", "Temur", "Tempo",
    "Tempest Hawk", "Templar Knights", "The Ring", "Theft", "Thopters", "Time Counters", "Time Lords",
    "Tokens", "Toolbox", "Topdeck", "Toughness Matters", "Treasure", "Treefolk", "Triggered Abilities",
    "Tron", "Turbo Fog", "Turtles", "Tyranids", "Type Hack", "Umori Companion", "Unblockable", "Unicorns",
    "Unnatural", "Vampires", "Vanilla", "Vehicles", "Villainous Choice", "Voltron", "Voting", "Warriors",
    "Weenies", "Werewolves", "Whales", "Wheels", "Witch-Maw", "Wizards", "Wolves", "Wraiths", "Wurms",
    "X Spells", "Yore-Tiller", "Zirda Companion", "Zombies", "Zoo"
]

def filter_decks(decks, budget_query, tags_query):
    """
    Filters a list of decks based on budget and tag criteria.

    Returns:
        The first matching deck dictionary, or None if no match is found.
    """
    for deck in decks:
        is_match = True

        # 1. Filter by budget (if provided)
        if budget_query:
            price = deck.get('price', float('inf'))
            budget_match = False
            if "-" in budget_query:
                min_b, max_b = map(float, budget_query.split('-'))
                if min_b <= price <= max_b: budget_match = True
            elif ">" in budget_query:
                min_b = float(budget_query.replace('>', ''))
                if price >= min_b: budget_match = True
            elif "<" in budget_query:
                max_b = float(budget_query.replace('<', ''))
                if price <= max_b: budget_match = True
            else:  # A single number is treated as max budget
                max_b = float(budget_query)
                if price <= max_b: budget_match = True

            if not budget_match:
                is_match = False

        # 2. Filter by tags (if provided and still a match)
        if is_match and tags_query:
            search_tags = [t.strip() for t in tags_query.split(',') if t.strip()]
            deck_tags_lower = [t.lower() for t in deck.get("tags", [])]
            if not all(any(search_tag in deck_tag for deck_tag in deck_tags_lower) for search_tag in search_tags):
                is_match = False

        # If all active filters passed, we found our deck
        if is_match:
            return deck

    return None # No deck found

class MultiTagCompleter(QCompleter):
    """
    A custom QCompleter that handles comma-separated values.
    It suggests completions for the text segment after the last comma.
    """
    def __init__(self, model, parent=None):
        super().__init__(model, parent)

    def pathFromIndex(self, index):
        """
        Constructs the full text string when a completion is selected.
        """
        completion = super().pathFromIndex(index)
        current_text = self.widget().text()
        last_comma_pos = current_text.rfind(',')

        if last_comma_pos == -1:
            return completion

        prefix = current_text[:last_comma_pos]
        return f"{prefix.strip()}, {completion}"

    def splitPath(self, path):
        """
        Splits the text to determine which part to use for completion.
        """
        last_comma_pos = path.rfind(',')
        if last_comma_pos != -1:
            return [path[last_comma_pos + 1:].lstrip()]
        return [path]

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
        options.add_argument("--headless") # Run in background without opening a window
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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
        )

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
        card_list = list(card_map.values())
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

    def search(self):
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

        # --- SET STATUS ---
        status_text = "Looking for specified card..."
        self.errorLabel.setStyleSheet("background-color: lightgrey; color: black;")
        self.errorLabel.setText(status_text)
        self.errorLabel.setVisible(True)
        QApplication.processEvents()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "application/json;q=0.9,*/*;q=0.8"
        }

        query = f'{self.searchText.text()}'
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
                self.errorLabel.setText("Commander not found.")
                self.errorLabel.setVisible(True)
                return

            commander = json_data[0]
            self.data['commander'] = commander

            if self.partnerSearch.isChecked():
                if not self._handle_partner_search(commander, headers):
                    return
            else:
                image_uris = commander.get('image_uris')
                if image_uris:
                    image_link = image_uris.get('png')
                    filepath = "commander.png"
                    urllib.request.urlretrieve(image_link, filepath)
                    time.sleep(0.1)
                    self.original_commander_pixmap = QPixmap(filepath)
                elif "//" in commander.get("name"):
                    faces = commander.get("card_faces")
                    image_front_link = faces[0].get("image_uris", {}).get("png")
                    image_back_link = faces[1].get("image_uris", {}).get("png")
                    self.filepath_front = "commander_front.png"
                    self.filepath_back = "commander_back.png"
                    urllib.request.urlretrieve(image_front_link, self.filepath_front)
                    time.sleep(0.1)
                    urllib.request.urlretrieve(image_back_link, self.filepath_back)
                    time.sleep(0.1)
                    self.original_commander_pixmap = QPixmap(self.filepath_front)
                    self.commanderImageFlip.setEnabled(True)
                    self.commanderImageFlip.setVisible(True)
                else:
                    self.errorLabel.setText(f"No image found for {commander.get('name')}.")
                    self.errorLabel.setVisible(True)
                    return

            self.update_commander_image()
            status_text = "Commander found."
            self.errorLabel.setStyleSheet("background-color: lightgrey; color: black;")
            self.errorLabel.setText(status_text)

        except requests.exceptions.RequestException as e:
            self.errorLabel.setText(f"API request error: {e}")
            self.errorLabel.setVisible(True)
            self.commanderImage.setText("Failed to load data.")

    def search_random(self):
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

        # --- SET STATUS ---
        status_text = "Finding random commander..."
        self.errorLabel.setStyleSheet("background-color: lightgrey; color: black;")
        self.errorLabel.setText(status_text)
        self.errorLabel.setVisible(True)
        QApplication.processEvents()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "application/json;q=0.9,*/*;q=0.8"
        }

        query = f'{self.searchText.text()}'
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
            response.raise_for_status()
            commander = response.json()

            if not commander:
                self.errorLabel.setText("Commander not found.")
                self.errorLabel.setVisible(True)
                return

            self.data['commander'] = commander

            if self.partnerSearch.isChecked():
                if not self._handle_partner_search(commander, headers):
                    return
            else:
                image_uris = commander.get('image_uris')
                if image_uris:
                    image_link = image_uris.get('png')
                    filepath = "commander.png"
                    urllib.request.urlretrieve(image_link, filepath)
                    time.sleep(0.1)
                    self.original_commander_pixmap = QPixmap(filepath)
                elif "//" in commander.get("name"):
                    faces = commander.get("card_faces")
                    image_front_link = faces[0].get("image_uris", {}).get("png")
                    image_back_link = faces[1].get("image_uris", {}).get("png")
                    self.filepath_front = "commander_front.png"
                    self.filepath_back = "commander_back.png"
                    urllib.request.urlretrieve(image_front_link, self.filepath_front)
                    time.sleep(0.1)
                    urllib.request.urlretrieve(image_back_link, self.filepath_back)
                    time.sleep(0.1)
                    self.original_commander_pixmap = QPixmap(self.filepath_front)
                    self.commanderImageFlip.setEnabled(True)
                    self.commanderImageFlip.setVisible(True)
                else:
                    self.errorLabel.setText(f"No image found for {commander.get('name')}.")
                    self.errorLabel.setVisible(True)
                    return

            self.update_commander_image()
            status_text = "Commander found."
            self.errorLabel.setStyleSheet("background-color: lightgrey; color: black;")
            self.errorLabel.setText(status_text)

        except requests.exceptions.RequestException as e:
            self.errorLabel.setText(f"API request error: {e}")
            self.errorLabel.setVisible(True)
            self.commanderImage.setText("Failed to load data.")

    def _handle_partner_search(self, commander, headers):
        status_text = f"Looking up most popular partner for {commander.get('name')}..."
        self.errorLabel.setStyleSheet("background-color: lightgrey; color: black;")
        self.errorLabel.setText(status_text)
        self.errorLabel.setVisible(True)
        QApplication.processEvents()

        edhrec_link = commander.get("related_uris", {}).get("edhrec")
        if not edhrec_link:
            self.errorLabel.setText(f"No EDHRec link found for {commander.get('name')}.")
            self.errorLabel.setVisible(True)
            return False

        try:
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
            if not partner_list:
                self.errorLabel.setText(f"Could not find partner list for {commander.get('name')}.")
                self.errorLabel.setVisible(True)
                return False
            first_partner = partner_list.find("span", class_=re.compile("Card_name"))
            if not first_partner:
                self.errorLabel.setText(f"Could not find a partner for {commander.get('name')}.")
                self.errorLabel.setVisible(True)
                return False

            partner_name = first_partner.get_text()
            status_text = f"Most popular partner: {partner_name}. Fetching image..."
            self.errorLabel.setText(status_text)
            QApplication.processEvents()

            payload = {"order": "edhrec", "q": f'"{partner_name}" is:commander game:paper'}
            base_url = "https://api.scryfall.com/cards/search"
            fetch_partner = requests.get(base_url, params=payload, headers=headers)
            fetch_partner.raise_for_status()
            json_data = fetch_partner.json().get('data')
            if not json_data:
                self.errorLabel.setText(f"Could not find card data for partner: {partner_name}")
                self.errorLabel.setVisible(True)
                return False

            partner = json_data[0]
            self.data['partner'] = partner

            # Download commander image (including double-faced)
            c_image_uris = commander.get('image_uris')
            if c_image_uris:
                urllib.request.urlretrieve(c_image_uris.get('png'), "commander.png")
                self.original_commander_pixmap = QPixmap("commander.png")
            elif "//" in commander.get("name"):
                faces = commander.get("card_faces")
                urllib.request.urlretrieve(faces[0].get("image_uris", {}).get("png"), "commander_front.png")
                urllib.request.urlretrieve(faces[1].get("image_uris", {}).get("png"), "commander_back.png")
                self.filepath_front = "commander_front.png"
                self.filepath_back = "commander_back.png"
                self.original_commander_pixmap = QPixmap(self.filepath_front)
                self.commanderImageFlip.setEnabled(True)
                self.commanderImageFlip.setVisible(True)
            else:
                self.errorLabel.setText(f"No image found for {commander.get('name')}.")
                self.errorLabel.setVisible(True)
                return False # Cannot proceed without commander image

            # Download partner image
            p_image_uris = partner.get('image_uris', {})
            if p_image_uris:
                 urllib.request.urlretrieve(p_image_uris.get('png'), "partner.png")
                 self.original_partner_pixmap = QPixmap("partner.png")
                 self.partnerImage.setVisible(True)
            else:
                # Partners are not typically double-faced, but good to be safe
                self.errorLabel.setText(f"No image found for partner {partner.get('name')}.")
                self.errorLabel.setVisible(True)
                # We can proceed without the partner image, so we don't return False

            return True
        except requests.exceptions.RequestException as e:
            self.errorLabel.setText(f"API request error during partner search: {e}")
            self.errorLabel.setVisible(True)
            return False
        except Exception as e:
            self.errorLabel.setText(f"An error occurred during partner search: {e}")
            self.errorLabel.setVisible(True)
            return False

    def update_commander_image(self):
        """Scales the original pixmap and displays it in the label."""
        min_height = int(self.height() * (2 / 3))
        self.commanderImage.setMinimumHeight(min_height)
        self.partnerImage.setMinimumHeight(min_height)

        if not self.original_commander_pixmap:
            return

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

                budget_query = self.price_limit.text().strip()
                tags_query = self.tags_input.text().strip().lower()

                first_deck_found = None
                try:
                    first_deck_found = filter_decks(deck_table, budget_query, tags_query)
                except (ValueError, IndexError):
                    self.errorLabel.setText("Invalid budget format. Use numbers, '>', '<', or '-'.")
                    self.errorLabel.setVisible(True)
                    return

                if first_deck_found:
                    self.deckPriceLabel.setText(f"Decklist found for ${str(first_deck_found.get('price'))}")
                    self.deckPriceLabel.setEnabled(True)
                    deck_url_hash = first_deck_found.get("urlhash")
                    deck_link = f"https://edhrec.com/deckpreview/{deck_url_hash}"
                    status_text = f"Found deck within budget. Preparing to fetch..."
                    print(f"Found deck within budget: {deck_link}")
                    self.errorLabel.setStyleSheet("background-color: lightgrey; color: black;")
                    self.errorLabel.setText(status_text)
                    self.errorLabel.setVisible(True)
                    QApplication.processEvents()
                    self.data['deck_page'] = deck_link
                    self.copy_list_to_clipboard()
                else:
                    self.errorLabel.setText(f"No decks found matching your filters.")
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
                response_edhrec = requests.get(edhrec_link)
                response_edhrec.raise_for_status()

                deck_slug = response_edhrec.url
                name_slug = deck_slug.rsplit("/", 1)[-1]
                name_slug = name_slug.replace("?cc=", "")
                decks_site = f"https://edhrec.com/decks/{name_slug}"
                response = requests.get(decks_site)
                response.raise_for_status()

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

                budget_query = self.price_limit.text().strip()
                tags_query = self.tags_input.text().strip().lower()

                first_deck_found = None
                try:
                    first_deck_found = filter_decks(deck_table, budget_query, tags_query)
                except (ValueError, IndexError):
                    self.errorLabel.setText("Invalid budget format. Use numbers, '>', '<', or '-'.")
                    self.errorLabel.setVisible(True)
                    return

                if first_deck_found:
                    self.deckPriceLabel.setText(f"Decklist found for ${str(first_deck_found.get('price'))}")
                    self.deckPriceLabel.setEnabled(True)
                    deck_url_hash = first_deck_found.get("urlhash")
                    deck_link = f"https://edhrec.com/deckpreview/{deck_url_hash}"
                    status_text = f"Found deck within budget. Preparing to fetch..."
                    print(f"Found deck within budget: {deck_link}")
                    self.errorLabel.setStyleSheet("background-color: lightgrey; color: black;")
                    self.errorLabel.setText(status_text)
                    self.errorLabel.setVisible(True)
                    QApplication.processEvents()
                    self.data['deck_page'] = deck_link
                    self.copy_list_to_clipboard()
                else:
                    self.errorLabel.setText(f"No decks found matching your filters.")
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
