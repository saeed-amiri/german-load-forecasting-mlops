"""
Model registry and constructors for training models.
"""

from typing import Any

from sklearn.ensemble import GradientBoostingRegressor

MODEL_REGISTRY = {
    "gbr": GradientBoostingRegressor,
}


def get_model_class(model_id: str):
    """Return estimator class for a configured model identifier."""
    model_cls = MODEL_REGISTRY.get(model_id)
    if model_cls is None:
        available = ", ".join(sorted(MODEL_REGISTRY))
        raise ValueError(f"Unknown model_id '{model_id}'. Available: {available}")
    return model_cls


def build_model(model_id: str, params: dict[str, Any] | None = None):
    """Construct estimator instance using registry model id and params."""
    model_cls = get_model_class(model_id)
    return model_cls(**(params or {}))
