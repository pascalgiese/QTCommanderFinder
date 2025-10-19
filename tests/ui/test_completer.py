import pytest
from PyQt5.QtWidgets import QApplication, QLineEdit
from PyQt5.QtCore import QStringListModel

from src.ui.completer import MultiTagCompleter

@pytest.fixture
def completer_setup(qapp):
    """Fixture to set up a MultiTagCompleter with a QLineEdit."""
    model = QStringListModel(["tag1", "tag2", "long tag", "another tag"])
    completer = MultiTagCompleter(model)
    line_edit = QLineEdit()
    completer.setModel(model)
    completer.setWidget(line_edit)
    return completer, line_edit

def test_splitPath_single_tag(completer_setup):
    """Test splitPath with a single tag."""
    completer, line_edit = completer_setup
    line_edit.setText("tag")
    assert completer.splitPath("tag") == ["tag"]

def test_splitPath_multiple_tags(completer_setup):
    """Test splitPath with multiple comma-separated tags."""
    completer, line_edit = completer_setup
    line_edit.setText("tag1, anoth")
    assert completer.splitPath("tag1, anoth") == ["anoth"]
    line_edit.setText("tag1,tag2, long")
    assert completer.splitPath("tag1,tag2, long") == ["long"]

def test_pathFromIndex(completer_setup):
    """Test pathFromIndex to reconstruct the full text."""
    completer, line_edit = completer_setup
    line_edit.setText("tag1, ")
    # Simulate selecting "long tag" from completion for "long"
    mock_index = completer.model().index(2, 0) # Index for "long tag"
    result = completer.pathFromIndex(mock_index)
    assert result == "tag1, long tag"

    line_edit.setText("")
    mock_index = completer.model().index(0, 0) # Index for "tag1"
    result = completer.pathFromIndex(mock_index)
    assert result == "tag1"