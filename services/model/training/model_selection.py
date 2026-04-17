"""Model selection helpers for training runs."""

from configs.main import PipelineConfig


def resolve_model_name(config: PipelineConfig, model_name: str | None = None) -> str:
    """Resolve selected model key from request override, config default, or first configured model."""
    if model_name is not None:
        if model_name not in config.train.models:
            available = ", ".join(sorted(config.train.models))
            raise ValueError(f"Requested model '{model_name}' is unknown. Available models: {available}")
        return model_name

    if config.train.default_model is not None:
        if config.train.default_model not in config.train.models:
            available = ", ".join(sorted(config.train.models))
            raise ValueError(
                f"Configured default_model '{config.train.default_model}' is unknown. Available models: {available}"
            )
        return config.train.default_model

    if not config.train.models:
        raise ValueError("No models configured under train.models")

    return next(iter(config.train.models))
