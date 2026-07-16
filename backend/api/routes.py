"""FastAPI router for the Text Simplification API."""

import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from core.simplification_engine import SimplificationEngine
from core.providers.mock_provider import MockSimplificationProvider
from models.schemas import SimplifyRequest, SimplifyResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


def _build_engine() -> SimplificationEngine:
    """
    Construct the :class:`SimplificationEngine` based on environment config.

    ``PROVIDER=mistral`` activates :class:`MistralActivationSteeringProvider`.
    Any other value (including the default ``mock``) uses
    :class:`MockSimplificationProvider`.

    If the Mistral provider is requested but fails to initialise, the engine
    falls back to the mock provider and logs a warning.
    """
    provider_name = os.getenv("PROVIDER", "mock").strip().lower()

    if provider_name == "mistral":
        try:
            from core.providers.mistral_provider import MistralActivationSteeringProvider

            base_url = os.environ["MISTRAL_BASE_URL"]
            model = os.environ["MISTRAL_MODEL"]
            api_key = os.getenv("MISTRAL_API_KEY", "")
            steering_layer = int(os.getenv("MISTRAL_STEERING_LAYER", "16"))
            steering_coeff = float(os.getenv("MISTRAL_STEERING_COEFFICIENT", "8.0"))

            provider = MistralActivationSteeringProvider(
                base_url=base_url,
                model=model,
                api_key=api_key,
                steering_layer=steering_layer,
                steering_coefficient=steering_coeff,
            )
            logger.info("Using MistralActivationSteeringProvider (layer=%d)", steering_layer)
        except KeyError as exc:
            logger.warning(
                "PROVIDER=mistral but %s is not set — falling back to mock.", exc
            )
            provider = MockSimplificationProvider()
        except Exception as exc:
            logger.warning(
                "Failed to initialise Mistral provider (%s) — falling back to mock.", exc
            )
            provider = MockSimplificationProvider()
    else:
        provider = MockSimplificationProvider()
        logger.info("Using MockSimplificationProvider")

    strength_step = float(os.getenv("MISTRAL_STEERING_COEFFICIENT_STEP", "0.5"))
    return SimplificationEngine(provider=provider, strength_step=strength_step)


# Build engine once at module import (engine is stateless between requests)
_engine: SimplificationEngine = _build_engine()


@router.post("/simplify", response_model=SimplifyResponse)
async def simplify(request: SimplifyRequest) -> SimplifyResponse:
    """
    Simplify the provided text to the target Flesch–Kincaid grade level.

    The engine retries up to ``max_attempts`` times with increasing steering
    strength until the target is met or attempts are exhausted.
    """
    try:
        result = _engine.run(
            text=request.text,
            target_fk_grade=request.target_fk_grade,
            max_attempts=request.max_attempts,
        )
    except Exception as exc:
        logger.exception("Unexpected error during simplification: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SimplifyResponse(
        simplified_text=result.simplified_text,
        original_fk_grade=result.original_fk_grade,
        final_fk_grade=result.final_fk_grade,
        target_fk_grade=result.target_fk_grade,
        target_met=result.target_met,
        attempts=result.attempts,
        provider_mode=result.provider_mode,
        notes=result.notes,
    )
