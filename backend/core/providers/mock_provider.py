"""
Mock simplification provider.

This provider works fully offline without any model server or API keys.
It uses two lightweight heuristics to reduce the Flesch–Kincaid grade:

1. **Vocabulary substitution** — replaces long/complex words with shorter
   common-word alternatives from a built-in synonym map.
2. **Sentence splitting** — breaks overly long sentences (> ``MAX_WORDS``
   words) at conjunctions or commas to lower the average sentence length
   (which directly reduces FK grade via the words-per-sentence term).

The ``steering_strength`` parameter is interpreted as an aggression multiplier:
higher values apply heavier sentence splitting and wider synonym replacement.

Proper nouns, numbers, and words already in the top-1000 list are left alone.
"""

import re
from pathlib import Path
from typing import Set

from .base import BaseSimplificationProvider, SimplificationResult

# ---------------------------------------------------------------------------
# Synonym / replacement map (complex → simple)
# Only words whose replacements are clearly safe and meaning-preserving are
# included.  Proper nouns are intentionally absent.
# ---------------------------------------------------------------------------
SYNONYM_MAP: dict[str, str] = {
    "utilize": "use",
    "utilise": "use",
    "demonstrate": "show",
    "illustrate": "show",
    "communicate": "talk",
    "facilitate": "help",
    "implement": "do",
    "accomplish": "do",
    "acquire": "get",
    "obtain": "get",
    "purchase": "buy",
    "approximately": "about",
    "sufficient": "enough",
    "commence": "start",
    "initiate": "start",
    "terminate": "end",
    "conclude": "end",
    "additional": "more",
    "numerous": "many",
    "substantial": "big",
    "significant": "big",
    "require": "need",
    "necessitate": "need",
    "indicate": "show",
    "establish": "set up",
    "determine": "find",
    "construct": "build",
    "manufacture": "make",
    "encounter": "meet",
    "residence": "home",
    "individual": "person",
    "children": "kids",
    "difficult": "hard",
    "assistance": "help",
    "endeavor": "try",
    "endeavour": "try",
    "attempt": "try",
    "modification": "change",
    "alteration": "change",
    "component": "part",
    "element": "part",
    "regarding": "about",
    "concerning": "about",
    "consequently": "so",
    "therefore": "so",
    "nevertheless": "but",
    "however": "but",
    "although": "but",
    "moreover": "also",
    "furthermore": "also",
    "subsequently": "then",
    "previously": "before",
    "currently": "now",
    "immediately": "now",
    "specifically": "exactly",
    "particularly": "mostly",
    "primarily": "mainly",
    "generally": "usually",
    "typically": "usually",
    "frequently": "often",
    "occasionally": "sometimes",
    "extremely": "very",
    "absolutely": "very",
    "completely": "fully",
    "entirely": "fully",
    "various": "many",
    "several": "many",
    "numerous": "many",
    "majority": "most",
    "minority": "few",
    "category": "type",
    "classification": "type",
    "characteristics": "traits",
    "methodology": "method",
    "capability": "ability",
    "functionality": "feature",
    "terminology": "terms",
    "comprehend": "understand",
    "comprehension": "understanding",
    "observation": "note",
    "examination": "check",
    "investigation": "study",
    "resolution": "fix",
    "solution": "fix",
    "consideration": "thought",
    "implementation": "use",
    "documentation": "docs",
    "approximately": "about",
    "calculation": "math",
    "configuration": "setup",
    "fundamental": "basic",
    "sophisticated": "complex",
    "demonstrate": "show",
    "possess": "have",
    "provide": "give",
    "receive": "get",
    "perceive": "see",
    "observe": "see",
}

# Threshold for sentence splitting (words per sentence before splitting)
BASE_MAX_WORDS = 20


def _load_top_words(resource_path: Path) -> Set[str]:
    """Load top-1000 words from the resource file into a lowercase set."""
    if not resource_path.exists():
        return set()
    with open(resource_path, encoding="utf-8") as fh:
        return {line.strip().lower() for line in fh if line.strip()}


def _is_proper_noun(word: str) -> bool:
    """Heuristic: a word is a potential proper noun if it starts with a capital
    letter and is not at the start of a sentence context.  We conservatively
    treat any token that begins with an uppercase letter as potentially proper."""
    return len(word) > 0 and word[0].isupper()


def _replace_word(word: str, top_words: Set[str]) -> str:
    """Return a simplified replacement for *word* if one is available."""
    lower = word.lower()
    # Never touch proper nouns or numbers
    if _is_proper_noun(word) or re.match(r"^\d", word):
        return word
    # Already in common-word list — leave it
    if lower in top_words:
        return word
    replacement = SYNONYM_MAP.get(lower)
    if replacement is None:
        return word
    # Preserve leading capitalisation
    if word[0].isupper():
        return replacement.capitalize()
    return replacement


def _split_long_sentence(sentence: str, max_words: int) -> str:
    """
    Split a sentence that exceeds *max_words* words into shorter sentences.

    Splitting points: semicolons, then commas followed by a conjunction or
    a capital-letter continuation.
    """
    words = sentence.split()
    if len(words) <= max_words:
        return sentence

    # Try to split at " and ", " but ", " or ", " so ", " yet "
    conjunctions = re.compile(
        r"\b(and|but|or|so|yet|because|although|while|whereas)\b",
        re.IGNORECASE,
    )
    # Find a split point around the middle
    mid = len(words) // 2
    # Search within ±8 words of the midpoint for a conjunction
    search_start = max(0, mid - 8)
    search_end = min(len(words), mid + 8)
    partial = " ".join(words[search_start:search_end])
    m = conjunctions.search(partial)
    if m:
        # Compute absolute word index of the match
        before = " ".join(words[:search_start])
        abs_offset = len(before) + (1 if before else 0) + m.start()
        split_text = sentence[:abs_offset].rstrip(", ") + ". " + sentence[abs_offset:].lstrip().capitalize()
        return split_text

    # Fall back: hard split at mid with period
    first = " ".join(words[:mid])
    second = " ".join(words[mid:])
    if second:
        second = second[0].upper() + second[1:]
    return first + ". " + second


class MockSimplificationProvider(BaseSimplificationProvider):
    """
    Offline mock provider for end-to-end demonstrations.

    No GPU, no API key, no network access required.
    """

    PROVIDER_MODE = "mock"

    def __init__(self, resource_dir: Path | None = None):
        if resource_dir is None:
            resource_dir = Path(__file__).parent.parent.parent / "resources"
        top_words_path = resource_dir / "top_1000_words.txt"
        self._top_words = _load_top_words(top_words_path)

    def simplify(
        self,
        text: str,
        target_fk_grade: float,
        steering_strength: float = 1.0,
    ) -> SimplificationResult:
        """
        Apply vocabulary substitution and sentence splitting.

        ``steering_strength`` scales the aggressiveness:
        - ≤ 1.0 → standard substitution only
        - > 1.0 → also split long sentences, threshold decreasing with strength
        """
        result = self._apply_vocabulary(text)

        if steering_strength > 1.0:
            # Scale the max-words threshold down (more splits = lower FK)
            max_words = max(8, int(BASE_MAX_WORDS / steering_strength))
            result = self._apply_sentence_splitting(result, max_words)

        return SimplificationResult(
            simplified_text=result,
            provider_mode=self.PROVIDER_MODE,
            notes="Mock provider: vocabulary substitution + sentence splitting applied.",
        )

    def _apply_vocabulary(self, text: str) -> str:
        """Replace complex words with simpler alternatives."""
        tokens = re.split(r"(\s+)", text)
        result_tokens = []
        for token in tokens:
            if re.search(r"[a-zA-Z]", token):
                result_tokens.append(_replace_word(token, self._top_words))
            else:
                result_tokens.append(token)
        return "".join(result_tokens)

    def _apply_sentence_splitting(self, text: str, max_words: int) -> str:
        """Split long sentences in *text*."""
        # Split into sentences (preserve trailing punctuation)
        raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        simplified = []
        for sent in raw_sentences:
            simplified.append(_split_long_sentence(sent, max_words))
        return " ".join(simplified)
