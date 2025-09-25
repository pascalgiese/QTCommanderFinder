import pytest
from src.utils.deck_filter import filter_decks

@pytest.fixture
def sample_decks():
    """Provides a list of sample deck dictionaries for testing."""
    return [
        {"name": "Deck A", "price": 50.0, "tags": ["budget", "control"]},
        {"name": "Deck B", "price": 120.0, "tags": ["aggro", "midrange"]},
        {"name": "Deck C", "price": 80.0, "tags": ["combo", "budget", "tokens"]},
        {"name": "Deck D", "price": 250.0, "tags": ["cEDH", "combo"]},
        {"name": "Deck E", "price": 30.0, "tags": ["budget", "voltron"]},
    ]

def test_filter_decks_no_filters(sample_decks):
    """Test with no budget or tag filters."""
    assert filter_decks(sample_decks, "", "") == sample_decks[0]

def test_filter_decks_budget_max(sample_decks):
    """Test filtering by maximum budget."""
    assert filter_decks(sample_decks, "100", "") == sample_decks[0] # Deck A (50)
    assert filter_decks(sample_decks, "70", "") == sample_decks[0] # Deck A (50)
    assert filter_decks(sample_decks, "40", "") == sample_decks[4] # Deck E (30)
    assert filter_decks(sample_decks, "20", "") is None

def test_filter_decks_budget_range(sample_decks):
    """Test filtering by budget range."""
    assert filter_decks(sample_decks, "70-90", "") == sample_decks[2] # Deck C (80)
    assert filter_decks(sample_decks, "10-40", "") == sample_decks[4] # Deck E (30)
    assert filter_decks(sample_decks, "150-200", "") is None

def test_filter_decks_budget_min(sample_decks):
    """Test filtering by minimum budget."""
    assert filter_decks(sample_decks, ">100", "") == sample_decks[1] # Deck B (120)
    assert filter_decks(sample_decks, ">200", "") == sample_decks[3] # Deck D (250)
    assert filter_decks(sample_decks, ">300", "") is None

def test_filter_decks_budget_less_than(sample_decks):
    """Test filtering by less than budget."""
    assert filter_decks(sample_decks, "<60", "") == sample_decks[0] # Deck A (50)
    assert filter_decks(sample_decks, "<40", "") == sample_decks[4] # Deck E (30)
    assert filter_decks(sample_decks, "<20", "") is None

def test_filter_decks_single_tag(sample_decks):
    """Test filtering by a single tag."""
    assert filter_decks(sample_decks, "", "aggro") == sample_decks[1]
    assert filter_decks(sample_decks, "", "voltron") == sample_decks[4]
    assert filter_decks(sample_decks, "", "nonexistent") is None

def test_filter_decks_multiple_tags(sample_decks):
    """Test filtering by multiple tags."""
    assert filter_decks(sample_decks, "", "budget,control") == sample_decks[0]
    assert filter_decks(sample_decks, "", "combo,budget") == sample_decks[2]
    assert filter_decks(sample_decks, "", "aggro,control") is None

def test_filter_decks_budget_and_tags(sample_decks):
    """Test filtering by both budget and tags."""
    assert filter_decks(sample_decks, "100", "budget") == sample_decks[0] # Deck A (50, budget, control)
    assert filter_decks(sample_decks, "90", "combo") == sample_decks[2] # Deck C (80, combo, budget, tokens)
    assert filter_decks(sample_decks, "70", "aggro") is None # Deck B (120) is too expensive
    assert filter_decks(sample_decks, ">100", "budget") is None # No budget deck > 100