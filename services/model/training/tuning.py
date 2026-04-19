"""Hyperparameter tuning routines for training service."""

import json
import logging
import time
from datetime import datetime, timezone
from typing import cast

import joblib
import pyarrow as pa
from sklearn.base import BaseEstimator
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

from .context import TrainContext
from .model_factory import build_model
from .model_types import ModelParams

logger = logging.getLogger(__name__)


def _update_latest_params_pointer(ctx: TrainContext) -> None:
    """Update latest.json pointer to the newest best-params file for the model."""
    pointer_path = ctx.params_latest_pointer_file
    pointer_data = {
        "run_id": ctx.run_id,
        "model_name": ctx.model_name,
        "file_name": ctx.best_params_file.name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    pointer_path.write_text(json.dumps(pointer_data, indent=2), encoding="utf-8")


def find_best_params(X_train: pa.Table, y_train: pa.Table, ctx: TrainContext) -> ModelParams:
    """Search and persist best estimator parameters for the selected model."""
    start_time = time.perf_counter()

    tscv = TimeSeriesSplit(n_splits=ctx.cv_folds)
    base_model = cast(BaseEstimator, build_model(model_id=ctx.model_type))

    searcher = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=ctx.param_grid,
        n_iter=4,
        cv=tscv,
        scoring=ctx.scoring,
        n_jobs=4,
        verbose=1,
    )
    with joblib.parallel_backend("threading"):
        searcher.fit(X_train, y_train)

    best_params = cast(ModelParams, searcher.best_params_)
    joblib.dump(best_params, ctx.best_params_file)
    _update_latest_params_pointer(ctx)

    duration = time.perf_counter() - start_time
    logger.info(
        "In %.2f seconds, computed best parameters: %s, saved to %s",
        duration,
        best_params,
        ctx.best_params_file,
    )

    return best_params
