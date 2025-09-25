import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="session")
def qapp():
    """Fixture for QApplication, required by pytest-qt."""
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def mock_requests_get(mocker):
    """
    Mocks requests.get to return a configurable mock response.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None # Assume success by default
    mock_response.json.return_value = {}
    mock_response.text = ""
    mock_response.url = "http://mock.url"

    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

@pytest.fixture
def mock_urllib_urlretrieve(mocker):
    """
    Mocks urllib.request.urlretrieve to prevent actual file downloads.
    """
    mocker.patch("urllib.request.urlretrieve")

@pytest.fixture
def mock_selenium_driver(mocker):
    """
    Mocks selenium.webdriver.Chrome and its common methods.
    """
    # Import Chrome here to use it for the spec
    from selenium.webdriver import Chrome

    # Create a mock that passes isinstance(..., Chrome) checks
    mock_driver = MagicMock(spec=Chrome)
    mock_driver.get.return_value = None
    mock_driver.quit.return_value = None
    mock_driver.save_screenshot.return_value = None

    # Mock find_element and execute_script for Moxfield scraping
    mock_element = MagicMock()
    mock_element.get_attribute.return_value = "Mock Decklist Content"
    mock_driver.find_element.return_value = mock_element
    mock_driver.execute_script.return_value = None

    # Mock WebDriverWait and expected_conditions
    mock_wait = MagicMock()
    mock_wait.until.return_value = mock_element # For element_to_be_clickable, visibility_of_element_located
    mocker.patch("selenium.webdriver.support.ui.WebDriverWait", return_value=mock_wait)
    mocker.patch("selenium.webdriver.support.expected_conditions.element_to_be_clickable", return_value=lambda _: True)
    mocker.patch("selenium.webdriver.support.expected_conditions.visibility_of_element_located", return_value=lambda _: True)
    mocker.patch("selenium.webdriver.support.expected_conditions.presence_of_element_located", return_value=lambda _: True)

    # Mock BeautifulSoup for Archidekt scraping
    mock_soup = MagicMock()
    mock_script_tag = MagicMock()
    mock_script_tag.string = '{"props": {"pageProps": {"redux": {"deck": {"cardMap": {"1": {"qty": 1, "name": "Card A", "setCode": "SET", "collectorNumber": "1", "categories": []}}}}}}}}'
    mock_soup.find.return_value = mock_script_tag
    mocker.patch("bs4.BeautifulSoup", return_value=mock_soup)

    # Mock selenium_stealth
    mocker.patch("selenium_stealth.stealth")

    # Patch webdriver.Chrome directly
    mocker.patch("selenium.webdriver.Chrome", return_value=mock_driver, autospec=True)

    yield mock_driver