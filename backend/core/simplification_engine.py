"""
SimplificationEngine — orchestrates the simplification retry loop.

Algorithm
---------
1. Calculate the original FK grade.
2. Call the provider to get a simplified candidate.
3. Calculate the candidate's FK grade.
4. If the target is met (candidate_fk ≤ target_fk), return immediately.
5. Otherwise increase the ``steering_strength`` by ``strength_step`` and retry.
6. After ``max_attempts``, return whichever candidate was closest to the target.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from .fk_calculator import flesch_kincaid_grade
from .providers.base import BaseSimplificationProvider

logger = logging.getLogger(__name__)


@dataclass
class EngineResult:
    """Full result returned by the simplification engine."""

    simplified_text: str
    original_fk_grade: float
    final_fk_grade: float
    target_fk_grade: float
    target_met: bool
    attempts: int
    provider_mode: str
    notes: Optional[str] = None


class SimplificationEngine:
    """
    Retry loop that drives the simplification provider until the target
    Flesch–Kincaid grade is achieved or ``max_attempts`` is exhausted.

    Parameters
    ----------
    provider:
        A :class:`~core.providers.base.BaseSimplificationProvider` instance.
    initial_strength:
        Starting ``steering_strength`` passed to the provider.
    strength_step:
        Amount added to ``steering_strength`` on each unsuccessful retry.
    """

    def __init__(
        self,
        provider: BaseSimplificationProvider,
        initial_strength: float = 1.0,
        strength_step: float = 0.5,
    ):
        self._provider = provider
        self._initial_strength = initial_strength
        self._strength_step = strength_step

    def run(
        self,
        text: str,
        target_fk_grade: float,
        max_attempts: int = 5,
    ) -> EngineResult:
        """
        Simplify *text* aiming for *target_fk_grade*.

        Returns
        -------
        EngineResult
            The best simplification found within *max_attempts* retries.
        """
        original_fk = flesch_kincaid_grade(text)
        logger.info("Original FK grade: %.2f | target: %.2f", original_fk, target_fk_grade)

        best_text: Optional[str] = None
        best_fk: float = float("inf")
        best_notes: Optional[str] = None
        provider_mode: str = "unknown"
        strength = self._initial_strength

        for attempt in range(1, max_attempts + 1):
            logger.info("Attempt %d/%d (strength=%.2f)", attempt, max_attempts, strength)
            try:
                result = self._provider.simplify(
                    text=text,
                    target_fk_grade=target_fk_grade,
                    steering_strength=strength,
                )
            except Exception as exc:
                logger.error("Provider error on attempt %d: %s", attempt, exc)
                strength += self._strength_step
                continue

            provider_mode = result.provider_mode
            candidate_fk = flesch_kincaid_grade(result.simplified_text)
            logger.info("Attempt %d FK grade: %.2f", attempt, candidate_fk)

            # Track the closest-to-target candidate
            if best_text is None or abs(candidate_fk - target_fk_grade) < abs(best_fk - target_fk_grade):
                best_text = result.simplified_text
                best_fk = candidate_fk
                best_notes = result.notes

            if candidate_fk <= target_fk_grade:
                logger.info("Target met on attempt %d", attempt)
                return EngineResult(
                    simplified_text=result.simplified_text,
                    original_fk_grade=original_fk,
                    final_fk_grade=candidate_fk,
                    target_fk_grade=target_fk_grade,
                    target_met=True,
                    attempts=attempt,
                    provider_mode=provider_mode,
                    notes=result.notes,
                )

            strength += self._strength_step

        # Return the best candidate found (target not met)
        logger.info(
            "Target not met after %d attempts. Best FK: %.2f (target %.2f)",
            max_attempts,
            best_fk,
            target_fk_grade,
        )
        return EngineResult(
            simplified_text=best_text or text,
            original_fk_grade=original_fk,
            final_fk_grade=best_fk if best_text else original_fk,
            target_fk_grade=target_fk_grade,
            target_met=False,
            attempts=max_attempts,
            provider_mode=provider_mode,
            notes=best_notes,
        )
