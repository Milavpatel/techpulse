"""
summarizer.py — Extractive text summarization utilities.

No external AI API required. Uses sentence scoring based on:
  - Term frequency within the article
  - Position bias (earlier sentences score higher)
  - Title-overlap bonus
"""

import re
from math import log


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_STOP_WORDS = set(
    "a an the is are was were be been being have has had do does did "
    "will would could should may might shall can cannot must to of in "
    "on at by for with as from that this these those it its we they "
    "he she you i me my our us your him her his hers their them said "
    "also but and or not nor so yet both either neither just very".split()
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-z]{3,}\b", text.lower())


def _sentence_split(text: str) -> list[str]:
    # Split on sentence-ending punctuation followed by whitespace + uppercase
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def _term_freq(tokens: list[str]) -> dict[str, float]:
    freq: dict[str, float] = {}
    for tok in tokens:
        if tok not in _STOP_WORDS:
            freq[tok] = freq.get(tok, 0) + 1
    max_f = max(freq.values(), default=1)
    return {k: v / max_f for k, v in freq.items()}


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def summarize(text: str, title: str = "", num_sentences: int = 3) -> str:
    """
    Return an extractive summary of *text* as a single paragraph.
    Falls back to the first `num_sentences` sentences if text is short.
    """
    if not text:
        return ""

    sentences = _sentence_split(text)
    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    tokens   = _tokenize(text)
    tf       = _term_freq(tokens)
    t_tokens = set(_tokenize(title)) - _STOP_WORDS

    scores: list[tuple[float, int, str]] = []
    for idx, sent in enumerate(sentences):
        s_tokens = _tokenize(sent)
        # TF score
        score = sum(tf.get(t, 0) for t in s_tokens if t not in _STOP_WORDS)
        # Position boost (earlier = better)
        score *= 1 / (1 + log(idx + 1))
        # Title overlap bonus
        overlap = len(set(s_tokens) & t_tokens)
        score += overlap * 0.5
        scores.append((score, idx, sent))

    top = sorted(scores, key=lambda x: x[0], reverse=True)[:num_sentences]
    # Restore original order
    top.sort(key=lambda x: x[1])
    return " ".join(s for _, _, s in top)


def bullet_points(text: str, title: str = "", n: int = 4) -> list[str]:
    """Return up to *n* bullet-point key sentences."""
    summary = summarize(text, title=title, num_sentences=n)
    sentences = _sentence_split(summary) or _sentence_split(text)
    return sentences[:n]


def reading_time(text: str) -> str:
    """Estimate reading time based on average 200 wpm."""
    word_count = len(text.split())
    minutes = max(1, round(word_count / 200))
    return f"{minutes} min read"


def extract_keywords(text: str, title: str = "", top_n: int = 6) -> list[str]:
    """Extract the top N meaningful keywords from title + text."""
    combined = f"{title} {text}"
    tokens   = _tokenize(combined)
    tf       = _term_freq(tokens)
    # Filter very common tech words that add no info
    noise = {"like", "use", "new", "make", "get", "one", "two", "way", "need", "help"}
    ranked = sorted(
        [(w, s) for w, s in tf.items() if w not in noise],
        key=lambda x: x[1],
        reverse=True,
    )
    return [w.capitalize() for w, _ in ranked[:top_n]]
