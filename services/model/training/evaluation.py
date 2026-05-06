"""Evaluation routines for training service."""

import pyarrow as pa
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .model_types import RegressorModel


def evaluate_regression(model: RegressorModel, X_test: pa.Table, y_test: pa.Array) -> dict[str, float]:
    """Return baseline regression metrics for a fitted model."""
    prediction = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, prediction))
    mse = float(mean_squared_error(y_test, prediction))
    r2 = float(model.score(X_test, y_test))

    return {
        "mae": mae,
        "mse": mse,
        "r2": r2,
    }
