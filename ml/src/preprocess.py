import re
import string

import nltk
from nltk.corpus import stopwords

# Download stopwords once when the module is first imported.
try:
    _BASE_STOP_WORDS = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords", quiet=True)
    _BASE_STOP_WORDS = set(stopwords.words("english"))

# Words critical for intent, negation, and priority that must NOT be removed
PRESERVED_WORDS = {
    "not", "no", "never", "unable", "cannot", "without", "against",
    "down", "fail", "failed", "failing", "error", "crashed", "urgent"
}

_STOP_WORDS = _BASE_STOP_WORDS - PRESERVED_WORDS


def preprocess_text(text: str) -> str:
    """
    Clean ticket text for ML models.

    Steps:
    1. Safe string conversion
    2. Convert to lowercase
    3. Remove punctuation
    4. Remove non-negation English stopwords
    """
    if not isinstance(text, str):
        text = str(text)

    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = text.split()
    words = [word for word in words if word not in _STOP_WORDS]
    return " ".join(words)
