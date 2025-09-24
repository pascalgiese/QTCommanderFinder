# D:/Python Projekte/tests/test_gui.py
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from qtcommanderfinder import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Mock-Antwort von der Scryfall-API
MOCK_SCRYFALL_RESPONSE = {
    "data": [
        {
            "name": "Test Commander",
            "image_uris": {"png": "fake_url"},
            "related_uris": {"edhrec": "fake_edhrec_url"}
        }
    ]
}

@pytest.fixture
def app(qtbot):
    """Erstellt eine Instanz unserer Anwendung für jeden Test."""
    test_app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_search_success(app, qtbot, mocker):
    """Testet den erfolgreichen Such-Workflow."""
    # Mocke die 'requests.get'-Funktion, damit wir nicht ins Internet gehen
    mock_get = mocker.patch("requests.get")
    # Konfiguriere den Mock, um unsere Beispieldaten zurückzugeben
    mock_get.return_value.json.return_value = MOCK_SCRYFALL_RESPONSE
    mock_get.return_value.raise_for_status.return_value = None

    # Mocke das Herunterladen des Bildes
    mocker.patch("urllib.request.urlretrieve")

    # Simuliere Nutzereingaben
    app.searchText.setText("Test Commander")
    qtbot.mouseClick(app.searchButton, Qt.LeftButton)

    # Überprüfe das Ergebnis
    assert app.errorLabel.text() == "Commander found."
    assert app.data["commander"]["name"] == "Test Commander"