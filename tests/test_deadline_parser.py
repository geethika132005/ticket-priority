import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from deadline_parser import extract_deadline


def test_extract_deadline_asap():
    text = "Please resolve this server error asap"
    result = extract_deadline(text)
    assert result is not None
    assert result.lower() == "asap"


def test_extract_deadline_day_name():
    text = "Need access approved by Friday morning"
    result = extract_deadline(text)
    assert result is not None
    assert "by Friday" in result or "friday" in result.lower()


def test_extract_deadline_time():
    text = "Deploy hotfix before 5 PM today"
    result = extract_deadline(text)
    assert result is not None
    assert "before 5 pm" in result.lower() or "5 pm" in result.lower()


def test_extract_deadline_within_duration():
    text = "SSL certificate expires within 2 days"
    result = extract_deadline(text)
    assert result is not None
    assert "within 2 days" in result.lower()


def test_extract_deadline_none():
    text = "Routine software update scheduled for regular maintenance"
    result = extract_deadline(text)
    assert result is None
