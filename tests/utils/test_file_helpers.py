import pytest
import os
import sys
from unittest.mock import patch

from src.utils.file_helpers import resource_path

@pytest.fixture(autouse=True)
def mock_os_path_abspath(mocker):
    """
    Mocks os.path.abspath to control the base path for resource_path.
    """
    # Assume project root is the current working directory for tests
    mocker.patch("os.path.abspath", return_value=os.getcwd())

def test_resource_path_dev_mode(mocker):
    """
    Test resource_path in development mode (without _MEIPASS).
    """
    mocker.patch.object(sys, '_MEIPASS', new=None) # Ensure _MEIPASS is not set
    expected_path = os.path.join(os.getcwd(), "assets", "flash-cards.png")
    assert resource_path(os.path.join("assets", "flash-cards.png")) == expected_path

def test_resource_path_pyinstaller_mode(mocker):
    """
    Test resource_path in PyInstaller mode (with _MEIPASS set).
    """
    mock_meipass = "/tmp/_MEIPASS_mock"
    mocker.patch.object(sys, '_MEIPASS', new=mock_meipass)
    expected_path = os.path.join(mock_meipass, "assets", "flash-cards.png")
    assert resource_path(os.path.join("assets", "flash-cards.png")) == expected_path