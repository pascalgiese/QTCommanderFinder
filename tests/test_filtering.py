# D:/Python Projekte/tests/test_filtering.py
import sys
import os

# Füge das src-Verzeichnis zum Python-Pfad hinzu, damit wir qtcommanderfinder importieren können
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from qtcommanderfinder import filter_decks

# Beispieldaten, die wir für unsere Tests verwenden
SAMPLE_DECKS = [
    {"price": 25.0, "tags": ["Budget", "Aggro"], "urlhash": "deck1"},
    {"price": 75.0, "tags": ["+1/+1 Counters", "Midrange"], "urlhash": "deck2"},
    {"price": 150.0, "tags": ["Stax", "Control"], "urlhash": "deck3"},
    {"price": 99.0, "tags": ["Budget", "+1/+1 Counters"], "urlhash": "deck4"},
]

def test_no_filters():
    """Sollte das erste Deck zurückgeben, wenn keine Filter gesetzt sind."""
    result = filter_decks(SAMPLE_DECKS, "", "")
    assert result is not None
    assert result["urlhash"] == "deck1"

def test_budget_filter_only():
    """Sollte das erste Deck unter 100 $ finden."""
    result = filter_decks(SAMPLE_DECKS, "<100", "")
    assert result is not None
    assert result["urlhash"] == "deck1"

def test_tags_filter_only():
    """Sollte das erste Deck mit dem Tag 'Counters' finden."""
    result = filter_decks(SAMPLE_DECKS, "", "counters")
    assert result is not None
    assert result["urlhash"] == "deck2"

def test_combined_filter():
    """Sollte das Deck finden, das 'budget' UND 'counters' als Tags hat."""
    result = filter_decks(SAMPLE_DECKS, "", "budget, counters")
    assert result is not None
    assert result["urlhash"] == "deck4"

def test_no_match_found():
    """Sollte None zurückgeben, wenn kein Deck passt."""
    result = filter_decks(SAMPLE_DECKS, "<20", "stax")
    assert result is None