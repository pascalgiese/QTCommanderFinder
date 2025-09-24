# D:/Python Projekte/tests/test_e2e.py
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from qtcommanderfinder import DecklistScraperWorker


# Markiere diesen Test als "langsam", damit wir ihn überspringen können
@pytest.mark.slow
def test_moxfield_scraping():
    """Testet den kompletten Moxfield-Scraping-Prozess."""
    # Eine bekannte, einfache Deckliste
    moxfield_url = "https://moxfield.com/decks/u5VIKh0f80qYhzm7SnIdHw"  # Korvold Deck

    # Wir können den Worker direkt für den Test instanziieren und ausführen
    # (ohne die PyQt-Signale zu verwenden)
    worker = DecklistScraperWorker(moxfield_url)

    # Führe die run-Methode aus, aber fange das Ergebnis ab
    result = []
    worker.finished.connect(lambda text: result.append(text))
    worker.run()

    assert len(result) == 1
    decklist = result[0]
    assert "Error" not in decklist
    assert "Korvold, Fae-Cursed King" in decklist
    assert "Arcane Signet" in decklist  # Eine häufige Karte zum Überprüfen