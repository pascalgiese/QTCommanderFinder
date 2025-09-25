import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import QThread
import os

from src.scraping.scraper_worker import DecklistScraperWorker
from src.config.constants import DEBUG_SCREENSHOT_PATH_TPL, DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH

# Helper to clean up files created by tests
@pytest.fixture(autouse=True)
def cleanup_debug_screenshots():
    yield
    for f in [DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH, "debug_screenshot_moxfield.png", "debug_screenshot_archidekt.png"]:
        if os.path.exists(f):
            os.remove(f)

@pytest.fixture
def worker_thread():
    """Fixture to manage a QThread for the worker."""
    thread = QThread()
    yield thread
    thread.quit()
    thread.wait()

def test_scraper_worker_init():
    """Test initialization and site detection."""
    worker_mox = DecklistScraperWorker("https://moxfield.com/decks/abc")
    assert worker_mox.site == "moxfield"

    worker_arch = DecklistScraperWorker("https://archidekt.com/decks/123")
    assert worker_arch.site == "archidekt"

    worker_unknown = DecklistScraperWorker("https://example.com/deck")
    assert worker_unknown.site == "unknown"

def test_scrape_moxfield_success(worker_thread, mock_selenium_driver, qtbot):
    """Test Moxfield scraping with mocked Selenium."""
    worker = DecklistScraperWorker("https://moxfield.com/decks/test")
    worker.moveToThread(worker_thread)

    mock_selenium_driver.find_element.return_value.get_attribute.return_value = "1 Card A\n2 Card B"

    result = []
    worker.finished.connect(result.append)

    worker_thread.started.connect(worker.run)
    worker_thread.start()
    qtbot.wait_for(lambda: len(result) > 0, timeout=5000)

    assert result[0] == "1 Card A\n2 Card B"
    mock_selenium_driver.execute_script.call_count == 2 # For more_button and export_link
    mock_selenium_driver.quit.assert_called_once()

def test_scrape_archidekt_success(worker_thread, mock_selenium_driver, qtbot):
    """Test Archidekt scraping with mocked Selenium and BeautifulSoup."""
    worker = DecklistScraperWorker("https://archidekt.com/decks/test")
    worker.moveToThread(worker_thread)

    # Configure mock_selenium_driver's BeautifulSoup to return specific data
    mock_selenium_driver.page_source = '<html><body><script id="__NEXT_DATA__">{"props": {"pageProps": {"redux": {"deck": {"cardMap": {"1": {"qty": 1, "name": "Card A", "setCode": "SET", "collectorNumber": "1", "categories": []}, "2": {"qty": 2, "name": "Card B", "setCode": "SET", "collectorNumber": "2", "categories": ["Commander"]}}}}}}}}</script></body></html>'
    mock_selenium_driver.find_element.return_value = MagicMock() # For __NEXT_DATA__ presence check

    result = []
    worker.finished.connect(result.append)

    worker_thread.started.connect(worker.run)
    worker_thread.start()
    qtbot.wait_for(lambda: len(result) > 0, timeout=5000)

    expected_decklist = "2 Card B (SET) 2\n1 Card A (SET) 1" # Commander first, then sorted
    assert result[0] == expected_decklist
    mock_selenium_driver.quit.assert_called_once()