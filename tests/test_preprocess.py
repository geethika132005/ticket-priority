import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocess import preprocess_text


def test_preprocess_lowercasing():
    text = "SERVER IS DOWN IMMEDIATELY"
    cleaned = preprocess_text(text)
    assert cleaned.islower()
    assert "server" in cleaned


def test_preprocess_punctuation_removal():
    text = "Error 500! Database connection failed..."
    cleaned = preprocess_text(text)
    assert "!" not in cleaned
    assert "." not in cleaned
    assert "error 500 database connection failed" in cleaned or "database connection failed" in cleaned


def test_preprocess_stopword_removal():
    text = "The system is unable to process the request"
    cleaned = preprocess_text(text)
    words = cleaned.split()
    assert "the" not in words
    assert "is" not in words
    assert "system" in words
    assert "unable" in words
    assert "process" in words
    assert "request" in words


def test_preprocess_preserves_negations():
    cleaned = preprocess_text("Payment was not received for invoice")
    assert "not" in cleaned.split()
    assert "received" in cleaned.split()
    assert "payment" in cleaned.split()


def test_preprocess_non_string():
    assert preprocess_text(12345) == "12345"
    assert preprocess_text(None) == "none"
