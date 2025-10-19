import pytest
import os
import sys
from unittest.mock import patch

from src.utils.file_helpers import resource_path

def test_resource_path_dev_mode(mocker):
    """
    Test resource_path in development mode (without _MEIPASS).
    This test now mocks sys.argv and os.getcwd to create a predictable
    environment, independent of how the test runner is invoked.
    It simulates running a script from a defined project root.
    """
    # 1. Define a mock project root. This makes the test independent of the CWD.
    mock_project_root = "D:\\Python Projekte"
    mocker.patch('os.getcwd', return_value=mock_project_root)

    # 2. Simulate running 'main.py' from the project root.
    #    os.path.abspath will use our mocked os.getcwd().
    mock_script_path = "main.py"
    mocker.patch.object(sys, 'argv', [mock_script_path])

    # 3. Determine the expected path based on our predictable mocks.
    # The function's logic is: base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    # In our mock scenario, this resolves to mock_project_root.
    expected_path = os.path.join(mock_project_root, "assets", "flash-cards.png")

    # 4. Run the assertion
    assert resource_path(os.path.join("assets", "flash-cards.png")) == expected_path

def test_resource_path_pyinstaller_mode(mocker):
    """
    Test resource_path in PyInstaller mode (with _MEIPASS set).
    """
    mock_meipass = "/tmp/_MEIPASS_mock"
    # Patch sys._MEIPASS. create=True is necessary because this attribute
    # does not exist in a normal Python environment.
    mocker.patch('sys._MEIPASS', mock_meipass, create=True)
    expected_path = os.path.join(mock_meipass, "assets", "flash-cards.png")
    assert resource_path(os.path.join("assets", "flash-cards.png")) == expected_path
