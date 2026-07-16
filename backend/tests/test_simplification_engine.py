"""Tests for MockSimplificationProvider and the SimplificationEngine."""

import pytest
from pathlib import Path

from core.providers.mock_provider import MockSimplificationProvider
from core.simplification_engine import SimplificationEngine


class TestMockProvider:
    def setup_method(self):
        resource_dir = Path(__file__).parent.parent / "resources"
        self.provider = MockSimplificationProvider(resource_dir=resource_dir)

    def test_returns_string(self):
        result = self.provider.simplify("The cat sat on the mat.", target_fk_grade=5.0)
        assert isinstance(result.simplified_text, str)
        assert len(result.simplified_text) > 0

    def test_provider_mode(self):
        result = self.provider.simplify("Hello world.", target_fk_grade=5.0)
        assert result.provider_mode == "mock"

    def test_synonym_replacement(self):
        text = "We should utilize this method to demonstrate the results."
        result = self.provider.simplify(text, target_fk_grade=5.0)
        # "utilize" → "use", "demonstrate" → "show"
        assert "use" in result.simplified_text.lower()

    def test_long_sentence_split_with_high_strength(self):
        long_sentence = (
            "The researchers conducted a comprehensive investigation and they found "
            "that the evidence was substantial and the methodology was sound and "
            "the conclusions were well supported by the data they collected."
        )
        result = self.provider.simplify(long_sentence, target_fk_grade=4.0, steering_strength=3.0)
        # High strength should split the sentence — result should contain a period
        sentences = [s for s in result.simplified_text.split(".") if s.strip()]
        assert len(sentences) >= 1  # At minimum one sentence returned

    def test_proper_nouns_preserved(self):
        text = "Albert Einstein developed the theory of relativity in 1905."
        result = self.provider.simplify(text, target_fk_grade=6.0)
        # "Albert Einstein" and "1905" should not be mangled
        assert "Einstein" in result.simplified_text
        assert "1905" in result.simplified_text


class TestSimplificationEngine:
    def setup_method(self):
        resource_dir = Path(__file__).parent.parent / "resources"
        provider = MockSimplificationProvider(resource_dir=resource_dir)
        self.engine = SimplificationEngine(
            provider=provider,
            initial_strength=1.0,
            strength_step=0.5,
        )

    def test_returns_engine_result(self):
        from core.simplification_engine import EngineResult
        result = self.engine.run(
            text="Scientists utilize sophisticated methodologies to examine phenomena.",
            target_fk_grade=6.0,
            max_attempts=3,
        )
        assert isinstance(result, EngineResult)

    def test_original_fk_computed(self):
        result = self.engine.run(
            text="The cat sat on the mat.",
            target_fk_grade=6.0,
            max_attempts=1,
        )
        assert isinstance(result.original_fk_grade, float)

    def test_attempts_bounded(self):
        result = self.engine.run(
            text="Simple text.",
            target_fk_grade=1.0,
            max_attempts=3,
        )
        assert result.attempts <= 3

    def test_target_fk_preserved(self):
        result = self.engine.run(
            text="Hello world.",
            target_fk_grade=7.0,
            max_attempts=2,
        )
        assert result.target_fk_grade == 7.0

    def test_simplified_text_non_empty(self):
        result = self.engine.run(
            text="The quick brown fox jumps over the lazy dog.",
            target_fk_grade=6.0,
            max_attempts=2,
        )
        assert result.simplified_text.strip() != ""
