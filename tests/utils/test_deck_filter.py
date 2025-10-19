import pytest
from src.utils.deck_filter import filter_decks

@pytest.fixture
def sample_decks():
    """Provides a list of sample deck dictionaries for testing."""
    return [
        {"name": "Deck A", "price": 50.0, "tags": ["budget", "control"], "salt": 40.0},
        {"name": "Deck B", "price": 120.0, "tags": ["aggro", "midrange"], "salt": 28.0},
        {"name": "Deck C", "price": 80.0, "tags": ["combo", "budget", "tokens"], "salt": 35.0},
        {"name": "Deck D", "price": 250.0, "tags": ["cEDH", "combo"], "salt": 45.0},
        {"name": "Deck E", "price": 30.0, "tags": ["budget", "voltron"], "salt": 20.0},
    ]

def test_filter_decks_no_filters(sample_decks):
    """Test with no budget or tag filters."""
    assert filter_decks(sample_decks, "", "", "") == sample_decks[0]

def test_filter_decks_budget_max(sample_decks):
    """Test filtering by maximum budget."""
    assert filter_decks(sample_decks, "100", "", "") == sample_decks[0] # Deck A (50)
    assert filter_decks(sample_decks, "70", "", "") == sample_decks[0] # Deck A (50)
    assert filter_decks(sample_decks, "40", "", "") == sample_decks[4] # Deck E (30)
    assert filter_decks(sample_decks, "20", "", "") is None

def test_filter_decks_budget_range(sample_decks):
    """Test filtering by budget range."""
    assert filter_decks(sample_decks, "70-90", "", "") == sample_decks[2] # Deck C (80)
    assert filter_decks(sample_decks, "10-40", "", "") == sample_decks[4] # Deck E (30)
    assert filter_decks(sample_decks, "150-200", "", "") is None

def test_filter_decks_budget_min(sample_decks):
    """Test filtering by minimum budget."""
    assert filter_decks(sample_decks, ">100", "", "") == sample_decks[1] # Deck B (120)
    assert filter_decks(sample_decks, ">200", "", "") == sample_decks[3] # Deck D (250)
    assert filter_decks(sample_decks, ">300", "", "") is None

def test_filter_decks_budget_less_than(sample_decks):
    """Test filtering by less than budget."""
    assert filter_decks(sample_decks, "<60", "", "") == sample_decks[0] # Deck A (50)
    assert filter_decks(sample_decks, "<40", "", "") == sample_decks[4] # Deck E (30)
    assert filter_decks(sample_decks, "<20", "", "") is None

def test_filter_decks_single_tag(sample_decks):
    """Test filtering by a single tag."""
    assert filter_decks(sample_decks, "", "aggro", "") == sample_decks[1]
    assert filter_decks(sample_decks, "", "voltron", "") == sample_decks[4]
    assert filter_decks(sample_decks, "", "nonexistent", "") is None

def test_filter_decks_multiple_tags(sample_decks):
    """Test filtering by multiple tags."""
    assert filter_decks(sample_decks, "", "budget,control", "") == sample_decks[0]
    assert filter_decks(sample_decks, "", "combo,budget", "") == sample_decks[2]
    assert filter_decks(sample_decks, "", "aggro,control", "") is None

def test_filter_decks_budget_and_tags(sample_decks):
    """Test filtering by both budget and tags."""
    assert filter_decks(sample_decks, "100", "budget", "") == sample_decks[0] # Deck A (50, budget, control)
    assert filter_decks(sample_decks, "90", "combo", "") == sample_decks[2] # Deck C (80, combo, budget, tokens)
    assert filter_decks(sample_decks, "70", "aggro", "") is None # Deck B (120) is too expensive
    assert filter_decks(sample_decks, ">100", "budget", "") is None # No budget deck > 100

def test_filter_decks_salt_max(sample_decks):
    assert filter_decks(sample_decks, "", "", "30") == sample_decks[1] # Deck B (Salt score 28)
    assert filter_decks(sample_decks, "", "", "40") == sample_decks[0] # Deck A (Salt score 40)
    assert filter_decks(sample_decks, "", "", "15") is None

def test_filter_decks_salt_range(sample_decks):
    assert filter_decks(sample_decks, "", "", "20-30") == sample_decks[1] # Deck B (Salt score between 20 and 30)
    assert filter_decks(sample_decks, "", "", "40-50") == sample_decks[0] # Deck A
    assert filter_decks(sample_decks, "", "", "45-50") == sample_decks[3] # Deck D
    assert filter_decks(sample_decks, "", "", "50-60") is None

def test_filter_decks_salt_min(sample_decks):
    assert filter_decks(sample_decks, "", "", ">30") == sample_decks[0] # Deck A (Salt score above 30)
    assert filter_decks(sample_decks, "", "", ">40") == sample_decks[3] # Deck D
    assert filter_decks(sample_decks, "", "", ">50") is None

def test_filter_decks_salt_and_budget(sample_decks):
    assert filter_decks(sample_decks, "120", "", "30") == sample_decks[1] # Deck B
    assert filter_decks(sample_decks, "60-100", "", "40") == sample_decks[2] # Deck C
    assert filter_decks(sample_decks, "200-300", "", ">30") == sample_decks[3]
    assert filter_decks(sample_decks, "300-400", "", ">40") is None

def test_filter_decks_all_parameters(sample_decks):
    assert filter_decks(sample_decks, "50-80", "budget,control", "<45") == sample_decks[0]
    assert filter_decks(sample_decks, "<200", "aggro", "<30") == sample_decks[1]
    assert filter_decks(sample_decks, "<300", "voltron", "<30") == sample_decks[4]
    assert filter_decks(sample_decks, "<300", "atogatog", "<40") is None