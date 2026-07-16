"""
Flesch–Kincaid Grade Level calculator.

Formula:
    FK = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59

Syllable counting uses a heuristic that is reliable for standard English text
without needing a pronunciation dictionary.
"""

import re


def count_syllables(word: str) -> int:
    """Estimate the syllable count of an English word using heuristics."""
    word = word.lower().strip(".,;:!?\"'()-")
    if not word:
        return 0

    # Words of 3 characters or fewer are typically one syllable
    if len(word) <= 3:
        return 1

    # Remove silent trailing 'e'
    word = re.sub(r"e$", "", word)

    # Count vowel groups; treat 'y' as a vowel when it follows a consonant
    # and is not at the start of the word (e.g. "happy", "funny", "system")
    vowel_groups = re.findall(r"[aeiou]+|(?<=[^aeiou\W])y", word)
    count = len(vowel_groups)

    # Adjustments
    # 'le' at end counts as a syllable (e.g., "able", "title")
    if word.endswith("le") and len(word) > 2 and word[-3] not in "aeiou":
        count += 1
    # 'ed' ending that is silent (e.g., "walked" → 1 extra syllable removed already)
    if word.endswith("ed") and len(word) > 2 and word[-3] not in "aeiou":
        count = max(1, count - 1)
    # 'es' ending
    if word.endswith("es") and len(word) > 3 and word[-3] not in "aeiou":
        count = max(1, count - 1)

    return max(1, count)


def count_sentences(text: str) -> int:
    """Count sentences by splitting on terminal punctuation."""
    sentences = re.split(r"[.!?]+", text.strip())
    # Filter out empty strings that result from split
    sentences = [s.strip() for s in sentences if s.strip()]
    return max(1, len(sentences))


def count_words(text: str) -> list[str]:
    """Return a list of words (tokens that start with an alphabetic character or digit)."""
    return re.findall(r"\b[a-zA-Z0-9'\-]+\b", text)


def flesch_kincaid_grade(text: str) -> float:
    """
    Calculate the Flesch–Kincaid Grade Level for the given text.

    Returns a float rounded to two decimal places. Returns 0.0 for empty/
    single-word texts to avoid division errors.
    """
    if not text or not text.strip():
        return 0.0

    words = count_words(text)
    word_count = len(words)
    if word_count == 0:
        return 0.0

    sentence_count = count_sentences(text)
    syllable_count = sum(count_syllables(w) for w in words)

    grade = (
        0.39 * (word_count / sentence_count)
        + 11.8 * (syllable_count / word_count)
        - 15.59
    )
    return round(grade, 2)
