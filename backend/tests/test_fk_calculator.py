"""Tests for the Flesch–Kincaid grade level calculator."""

import pytest
from core.fk_calculator import (
    count_syllables,
    count_sentences,
    count_words,
    flesch_kincaid_grade,
)


class TestCountSyllables:
    def test_single_vowel_word(self):
        assert count_syllables("a") >= 1

    def test_one_syllable_word(self):
        assert count_syllables("cat") == 1

    def test_two_syllable_word(self):
        assert count_syllables("happy") == 2

    def test_three_syllable_word(self):
        assert count_syllables("beautiful") >= 3

    def test_silent_e(self):
        # "make" → 1 syllable (silent e removed)
        assert count_syllables("make") == 1

    def test_minimum_one(self):
        # Every word should have at least 1 syllable
        for w in ["the", "a", "I", "ox"]:
            assert count_syllables(w) >= 1


class TestCountSentences:
    def test_single_sentence(self):
        assert count_sentences("Hello world.") == 1

    def test_two_sentences(self):
        assert count_sentences("Hello. World.") == 2

    def test_question_and_exclamation(self):
        assert count_sentences("Really? Yes!") == 2

    def test_empty_string(self):
        # Empty → treated as 1 sentence to avoid division by zero
        assert count_sentences("") == 1

    def test_no_punctuation(self):
        # No terminal punctuation — treated as 1 sentence
        assert count_sentences("This is a sentence without punctuation") == 1


class TestCountWords:
    def test_basic(self):
        assert len(count_words("hello world")) == 2

    def test_punctuation_stripped(self):
        words = count_words("Hello, world!")
        assert "Hello" in words
        assert "world" in words

    def test_empty(self):
        assert count_words("") == []

    def test_numbers_included(self):
        words = count_words("I have 3 cats")
        assert "3" in words


class TestFleschKincaidGrade:
    def test_empty_returns_zero(self):
        assert flesch_kincaid_grade("") == 0.0

    def test_grade_increases_with_complexity(self):
        simple = "The cat sat on the mat. The dog ran."
        complex_text = (
            "The systematic utilization of sophisticated methodologies "
            "fundamentally transforms organizational capabilities and institutional frameworks."
        )
        assert flesch_kincaid_grade(simple) < flesch_kincaid_grade(complex_text)

    def test_returns_float(self):
        result = flesch_kincaid_grade("Hello world.")
        assert isinstance(result, float)

    def test_non_negative(self):
        # Very simple text — FK can be negative, but formula output should be
        # a real number (not NaN/inf)
        result = flesch_kincaid_grade("The cat sat.")
        assert not (result != result)  # not NaN
        assert result != float("inf")

    def test_realistic_grade_range(self):
        text = (
            "Scientists discovered that the ancient artifact contains "
            "extraordinary inscriptions that illuminate historical civilizations."
        )
        grade = flesch_kincaid_grade(text)
        # Should be in a plausible range for this kind of text
        assert -5 < grade < 25
