"""
Mistral Activation Steering Provider.

⚠️  IMPORTANT — READ BEFORE USING ⚠️
======================================
Genuine *activation steering* modifies the internal hidden states of a
transformer model during the forward pass by adding a learned (or hand-crafted)
"steering vector" to a specific residual stream layer.  This is fundamentally
a **server-side / GPU-side** operation: the vector is computed or stored on
the server that hosts the model weights, and it is applied during inference.

There is **no way** to perform real activation steering from an Android client
or from a standard REST call to an unmodified OpenAI-compatible endpoint.
The pattern implemented here assumes you are running a custom inference
server — such as a patched version of vLLM, TGI, or a purpose-built
steering server — that:

1. Accepts steering configuration (layer index, steering vector / coefficient)
   as extra fields in the request body (or via headers/model parameters).
2. Applies the steering vector to the specified hidden-state layer during the
   model's forward pass.
3. Returns the steered completion as a standard chat-completion response.

The ``MISTRAL_BASE_URL``, ``MISTRAL_MODEL``, ``MISTRAL_API_KEY``,
``MISTRAL_STEERING_LAYER``, and ``MISTRAL_STEERING_COEFFICIENT`` environment
variables configure this provider.  See ``.env.example`` for details.

If the server is unreachable or returns an error, the engine falls back to
the mock provider (configurable via the ``PROVIDER`` env var).

Actual steering vector values depend on the deployed model's architecture and
must be pre-computed offline (e.g. using representation engineering or
CAA — Contrastive Activation Addition).  This file documents the *interface*;
supplying valid vectors is the operator's responsibility.
"""

import logging
from typing import Optional

import httpx

from .base import BaseSimplificationProvider, SimplificationResult

logger = logging.getLogger(__name__)

# System prompt that instructs the model to produce plain, readable output.
_SYSTEM_PROMPT = (
    "You are a text-simplification assistant. "
    "Rewrite the following text so that it is easy to understand. "
    "Use short sentences, simple common words, and plain language. "
    "Do not change proper nouns, numbers, or essential technical terms. "
    "Return only the simplified text, no explanations."
)


def _steering_system_prompt(target_grade: float, strength: float) -> str:
    """Build a prompt that communicates the target grade and steering strength."""
    return (
        f"{_SYSTEM_PROMPT} "
        f"Aim for a Flesch-Kincaid Grade Level of approximately {target_grade:.1f}. "
        f"Simplification intensity: {strength:.1f} (higher means simpler)."
    )


class MistralActivationSteeringProvider(BaseSimplificationProvider):
    """
    Provider that calls a Mistral-compatible model server with optional
    activation-steering parameters.

    Configuration (environment variables, loaded externally and passed in):
    - base_url: str        — server base URL (e.g. http://localhost:8080)
    - model: str           — model identifier on the server
    - api_key: str         — bearer token / API key (may be empty)
    - steering_layer: int  — transformer layer index to inject the vector
    - steering_coefficient: float — initial scaling factor for the vector
    - timeout: float       — HTTP timeout in seconds (default 60)

    See module docstring for a full explanation of what "activation steering"
    means and why a custom server is required.
    """

    PROVIDER_MODE = "mistral_activation_steering"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        steering_layer: int = 16,
        steering_coefficient: float = 8.0,
        timeout: float = 60.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._steering_layer = steering_layer
        self._steering_coefficient = steering_coefficient
        self._timeout = timeout

    def simplify(
        self,
        text: str,
        target_fk_grade: float,
        steering_strength: float = 1.0,
    ) -> SimplificationResult:
        """
        Send the text to the Mistral-compatible endpoint with steering params.

        The ``steering_strength`` multiplier scales ``steering_coefficient``,
        so repeated retries in the engine loop increase steering intensity.

        Request body follows the OpenAI chat-completions schema, extended with
        a ``steering`` object that a patched server understands:

        .. code-block:: json

            {
              "model": "mistral-7b-v0.1",
              "messages": [...],
              "steering": {
                "layer": 16,
                "coefficient": 12.0
              }
            }

        If your server uses a different schema, adapt this method accordingly.
        """
        effective_coeff = self._steering_coefficient * steering_strength
        system_msg = _steering_system_prompt(target_grade=target_fk_grade, strength=steering_strength)

        payload: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": text},
            ],
            # Non-standard extension for activation-steering servers
            "steering": {
                "layer": self._steering_layer,
                "coefficient": effective_coeff,
            },
            "max_tokens": 1024,
            "temperature": 0.3,
        }

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"******"

        url = f"{self._base_url}/v1/chat/completions"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Mistral server returned HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Could not reach Mistral server at {self._base_url}: {exc}"
            ) from exc

        try:
            simplified = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"Unexpected response structure from Mistral server: {data}"
            ) from exc

        return SimplificationResult(
            simplified_text=simplified,
            provider_mode=self.PROVIDER_MODE,
            notes=(
                f"Activation steering via {self._base_url} | "
                f"layer={self._steering_layer} coeff={effective_coeff:.1f}"
            ),
        )
