import pytest
import os
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.config.constants import (
    COMMANDER_IMG_PATH, COMMANDER_FRONT_IMG_PATH, COMMANDER_BACK_IMG_PATH,
    PARTNER_IMG_PATH, DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH
)

# Helper to clean up files created by tests
@pytest.fixture(autouse=True)
def cleanup_temp_files():
    yield
    for f in [COMMANDER_IMG_PATH, COMMANDER_FRONT_IMG_PATH, COMMANDER_BACK_IMG_PATH,
              PARTNER_IMG_PATH, DEBUG_SCREENSHOT_UNEXPECTED_ERROR_PATH,
              "debug_screenshot_moxfield.png", "debug_screenshot_archidekt.png"]:
        if os.path.exists(f):
            os.remove(f)

@pytest.fixture
def main_window(qtbot):
    """Fixture to create a MainWindow instance for testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_main_window_init(main_window):
    """Test that the main window initializes correctly."""
    main_window.setWindowTitle("QTCommanderFinder")
    assert main_window.windowTitle() == "QTCommanderFinder"
    assert main_window.searchText is not None
    assert main_window.searchButton is not None
    assert main_window.errorLabel is not None
    assert not main_window.errorLabel.isVisible()

def test_set_status(main_window, qtbot):
    """Test the _set_status method."""
    main_window._set_status("Test message", is_error=False)
    qtbot.waitUntil(lambda: main_window.errorLabel.text() == "Test message")
    assert main_window.errorLabel.text() == "Test message"
    assert "lightgrey" in main_window.errorLabel.styleSheet()

    main_window._set_status("Error message", is_error=True)
    qtbot.waitUntil(lambda: "red" in main_window.errorLabel.styleSheet())
    assert main_window.errorLabel.text() == "Error message"
    assert "red" in main_window.errorLabel.styleSheet()

def test_build_scryfall_query(main_window):
    """Test query construction."""
    main_window.searchText.setText("Teferi")
    query = main_window._build_scryfall_query()
    assert "Teferi is:commander game:paper" in query

    main_window.partnerSearch.setChecked(True)
    query = main_window._build_scryfall_query()
    assert "Teferi is:commander game:paper o:partner" in query

    main_window.searchText.setText("Teferi is:commander")
    query = main_window._build_scryfall_query()
    assert "Teferi is:commander game:paper o:partner" in query # Should not duplicate

def test_download_and_display_card_image_single_faced(main_window, mock_urllib_urlretrieve, mock_qpixmap, qtbot):
    """Test image download for a single-faced card."""
    card_data = {"name": "Test Commander", "image_uris": {"png": "http://example.com/test.png"}}
    result = main_window._download_and_display_card_image(card_data)
    assert result is True
    mock_urllib_urlretrieve.assert_called_with("http://example.com/test.png", COMMANDER_IMG_PATH)
    mock_qpixmap.assert_called_with(COMMANDER_IMG_PATH)
    assert not main_window.commanderImageFlip.isVisible()

def test_download_and_display_card_image_double_faced(main_window, mock_urllib_urlretrieve, mock_qpixmap):
    """Test image download for a double-faced card."""
    card_data = {
        "name": "Test DFC",
        "card_faces": [
            {"image_uris": {"png": "http://example.com/front.png"}},
            {"image_uris": {"png": "http://example.com/back.png"}}
        ]
    }
    result = main_window._download_and_display_card_image(card_data)
    assert result is True
    mock_urllib_urlretrieve.call_args_list[0].args == ("http://example.com/front.png", COMMANDER_FRONT_IMG_PATH)
    mock_urllib_urlretrieve.call_args_list[1].args == ("http://example.com/back.png", COMMANDER_BACK_IMG_PATH)
    mock_qpixmap.assert_called_with(COMMANDER_FRONT_IMG_PATH)
    assert main_window.commanderImageFlip.isEnabled()

def test_search_success(main_window, mock_requests_get, mock_urllib_urlretrieve, mock_qpixmap, qtbot):
    """Test a successful commander search."""
    mock_requests_get.json.return_value = {
        'data': [{'name': 'Test Commander', 'image_uris': {'png': 'http://example.com/test.png'}}]
    }
    main_window.searchText.setText("Test Commander")
    main_window.search()
    qtbot.waitUntil(lambda: main_window.data.get('commander') is not None, timeout=500)

    assert main_window.data['commander']['name'] == 'Test Commander'
    mock_urllib_urlretrieve.assert_called_once()
    assert main_window.errorLabel.text() == "Commander found."

def test_search_no_commander_found(main_window, mock_requests_get, qtbot):
    """Test search when no commander is found."""
    mock_requests_get.json.return_value = {'data': []}
    main_window.searchText.setText("NonExistent Commander")
    main_window.search()
    qtbot.waitUntil(lambda: main_window.errorLabel.text() == "Commander not found.", timeout=500)

    assert main_window.errorLabel.text() == "Commander not found."
    assert "red" in main_window.errorLabel.styleSheet()

def test_search_random_success(main_window, mock_requests_get, mock_urllib_urlretrieve, mock_qpixmap, qtbot):
    """Test a successful random commander search."""
    mock_requests_get.json.return_value = {'name': 'Random Commander', 'image_uris': {'png': 'http://example.com/random.png'}}
    main_window.search_random()
    qtbot.waitUntil(lambda: main_window.data.get('commander') is not None, timeout=500)

    assert main_window.data['commander']['name'] == 'Random Commander'
    mock_urllib_urlretrieve.assert_called_once()
    assert main_window.errorLabel.text() == "Commander found."

def test_handle_partner_search_success(main_window, mocker, mock_urllib_urlretrieve, mock_qpixmap, qtbot):
    """Test successful partner search."""
    commander_data = {
        "name": "Kydele, Chosen of Kruphix",
        "related_uris": {"edhrec": "http://edhrec.com/commanders/kydele-chosen-of-kruphix"},
        "image_uris": {"png": "http://example.com/kydele.png"} # Add image for commander
    }
    partner_data = {
        "name": "Ravos, Soultender",
        "image_uris": {"png": "http://example.com/ravos.png"}
    }

    # Mock EDHRec page for partner list
    mock_get = mocker.patch("src.ui.main_window.requests.get")
    mock_get.side_effect = [
        MagicMock(json=lambda: {'data': [commander_data]}, raise_for_status=lambda: None), # 1. The search() method's own Scryfall call
        # 2. _handle_partner_search's call to the EDHRec link to get the slug by following the redirect
        MagicMock(url="http://edhrec.com/commanders/kydele-chosen-of-kruphix", raise_for_status=lambda: None), # This mock is for the redirect
        # 3. The actual call to the partners page, which we mock to return the partner name
        MagicMock(text='<html><body><div class="cardlist"><span><span class="Card_name">Ravos, Soultender</span></span></div></body></html>', raise_for_status=lambda: None), # This mock is for the partners page
        MagicMock(json=lambda: {'data': [partner_data]}, raise_for_status=lambda: None), # Scryfall for partner
    ]

    main_window.partnerSearch.setChecked(True)
    main_window.searchText.setText(commander_data["name"]) # Set search text to trigger the logic
    # Call search() to trigger the full logic, not the private method directly
    main_window.search()
    qtbot.waitUntil(lambda: main_window.data.get('partner') is not None, timeout=1000)

    assert main_window.data['partner']['name'] == 'Ravos, Soultender'
    # Check that both images were downloaded
    assert mock_urllib_urlretrieve.call_count == 2
    assert main_window.errorLabel.text().startswith("Most popular partner: Ravos, Soultender.")

def test_flip_image(main_window, qtbot, mock_urllib_urlretrieve, mock_qpixmap):
    """Test the flip image functionality."""
    card_data = {
        "name": "Test DFC",
        "card_faces": [
            {"image_uris": {"png": "http://example.com/front.png"}},
            {"image_uris": {"png": "http://example.com/back.png"}}
        ]
    }
    main_window._download_and_display_card_image(card_data) # Setup DFC
    qtbot.wait(10)
    
    assert main_window.times_clicked_flip == 0

    main_window.flip_image()
    qtbot.wait(10)
    assert main_window.times_clicked_flip == 1

    main_window.flip_image()
    qtbot.wait(10)
    assert main_window.times_clicked_flip == 2
