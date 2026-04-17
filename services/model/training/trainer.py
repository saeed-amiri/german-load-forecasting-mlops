"""Model fitting routines for training service."""

from typing import Any

import pyarrow as pa

from .context import TrainContext
from .model_factory import build_model


def train_model(X_train: pa.Table, y_train: pa.Array, best_params: dict[str, Any], ctx: TrainContext) -> Any:
    """Fit and return model configured by model_id and selected parameters."""
    model = build_model(model_id=ctx.model_type, params=best_params)
    model.fit(X_train, y_train)
    return model
