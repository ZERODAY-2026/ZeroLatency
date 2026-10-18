"""Model allowlist, availability reporting and explicit (never automatic) model selection."""

from pydantic import BaseModel

from .config import SUPPORTED_MODELS
from .errors import ModelError, OllamaUnavailable, UnsupportedModel


def validate_model(model_id: object) -> str:
    """Exact-match allowlist check. No trimming, no case folding, no URLs, no fallback."""
    if not isinstance(model_id, str) or model_id not in SUPPORTED_MODELS:
        options = ", ".join(SUPPORTED_MODELS)
        raise UnsupportedModel(f"Unsupported model. Choose one of: {options}.")
    return model_id


def pull_hint(model_id: str) -> str:
    return f"ollama pull {model_id}"


class ModelInfo(BaseModel):
    id: str
    label: str
    installed: bool
    loaded: bool
    setup_hint: str | None = None


class ModelsStatus(BaseModel):
    ollama_available: bool
    ollama_version: str | None = None
    default_model: str
    models: list[ModelInfo]
    message: str | None = None


def models_status(client, default_model: str) -> ModelsStatus:
    """Report what the runtime actually has. Never claims a model is installed without checking."""
    try:
        installed = set(client.installed_models())
        loaded = set(client.loaded_models())
        version = client.version()
    except OllamaUnavailable:
        return ModelsStatus(
            ollama_available=False,
            default_model=default_model,
            models=[
                ModelInfo(id=m, label=label, installed=False, loaded=False, setup_hint=pull_hint(m))
                for m, label in SUPPORTED_MODELS.items()
            ],
            message="Cannot reach Ollama on the local endpoint. Start it with: ollama serve",
        )
    except ModelError:
        return ModelsStatus(
            ollama_available=True,
            default_model=default_model,
            models=[
                ModelInfo(id=m, label=label, installed=False, loaded=False, setup_hint=pull_hint(m))
                for m, label in SUPPORTED_MODELS.items()
            ],
            message="Ollama responded unexpectedly, so model availability is unknown.",
        )
    return ModelsStatus(
        ollama_available=True,
        ollama_version=version,
        default_model=default_model,
        models=[
            ModelInfo(
                id=m,
                label=label,
                installed=m in installed,
                loaded=m in loaded,
                setup_hint=None if m in installed else pull_hint(m),
            )
            for m, label in SUPPORTED_MODELS.items()
        ],
    )
