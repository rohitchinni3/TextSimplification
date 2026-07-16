"""
Abstract base class for simplification providers.

A *provider* is responsible for taking a piece of text and returning a
simplified version of it, given a target Flesch–Kincaid grade and an optional
steering strength hint.

Real activation-steering providers (e.g. MistralActivationSteeringProvider)
talk to a GPU-capable model server; the MockSimplificationProvider works
entirely in-process for demonstrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SimplificationResult:
    """Payload returned by a provider for one simplification attempt."""

    simplified_text: str
    provider_mode: str
    notes: Optional[str] = None


class BaseSimplificationProvider(ABC):
    """Common interface that every simplification provider must implement."""

    @abstractmethod
    def simplify(
        self,
        text: str,
        target_fk_grade: float,
        steering_strength: float = 1.0,
    ) -> SimplificationResult:
        """
        Simplify *text* aiming for *target_fk_grade*.

        Parameters
        ----------
        text:
            The source text to simplify.
        target_fk_grade:
            The desired Flesch–Kincaid Grade Level.
        steering_strength:
            A provider-specific hint for how aggressively to steer.
            Providers may ignore this if it is not applicable.

        Returns
        -------
        SimplificationResult
            Contains the simplified text and provider metadata.
        """
        ...
