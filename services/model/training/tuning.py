"""Hyperparameter tuning routines for training service."""

import logging
import time
from typing import Any

import joblib
import pyarrow as pa
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

from .context import TrainContext
from .model_factory import build_model

logger = logging.getLogger(__name__)


def find_best_params(X_train: pa.Table, y_train: pa.Table, ctx: TrainContext) -> dict[str, Any]:
    """Search and persist best estimator parameters for the selected model."""
    start_time = time.perf_counter()

    tscv = TimeSeriesSplit(n_splits=ctx.cv_folds)
    base_model = build_model(model_id=ctx.model_type)

    searcher = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=ctx.param_grid,
        cv=tscv,
        scoring=ctx.scoring,
        n_jobs=8,
        verbose=1,
    )
    searcher.fit(X_train, y_train)

    best_params = searcher.best_params_
    joblib.dump(best_params, ctx.best_params_file)

    duration = time.perf_counter() - start_time
    logger.info(
        "In %.2f seconds, computed best parameters: %s, saved to %s",
        duration,
        best_params,
        ctx.best_params_file,
    )

    return best_params
