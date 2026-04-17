"""Best-params loading and resolution helpers for training runs."""

import logging
from typing import cast

import joblib
import pyarrow as pa

from .context import TrainContext
from .model_types import ModelParams
from .tuning import find_best_params

logger = logging.getLogger(__name__)


def load_latest_best_params(ctx: TrainContext) -> ModelParams | None:
    """Load most recent best-params artifact for the selected model if available."""
    candidates = sorted(
        ctx.params_output_dir.glob(f"*.{ctx.ofmt}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None

    latest_file = candidates[0]
    try:
        params = cast(ModelParams, joblib.load(latest_file))
    except Exception as exc:
        logger.warning("Failed loading best params from %s: %s", latest_file, exc)
        return None

    logger.info("Loaded best params from %s", latest_file)
    return params


def resolve_best_params(
    x_train: pa.Table,
    y_train: pa.Table,
    ctx: TrainContext,
    use_saved_best_params: bool,
) -> ModelParams:
    """Resolve best params from saved artifact or by running hyperparameter search."""
    if use_saved_best_params:
        loaded_params = load_latest_best_params(ctx)
        if loaded_params is not None:
            return loaded_params
        logger.info(
            "No reusable best-params file found for model '%s' in %s. Running parameter search.",
            ctx.model_name,
            ctx.params_output_dir,
        )

    return find_best_params(x_train, y_train, ctx)
