"""Best-params loading and resolution helpers for training runs."""

import json
import logging
from typing import cast

import joblib
import pyarrow as pa

from .context import TrainContext
from .model_types import ModelParams
from .tuning import find_best_params

logger = logging.getLogger(__name__)


def _load_best_params_from_pointer(ctx: TrainContext) -> ModelParams | None:
    """Load best-params file pointed to by latest.json in model params directory."""
    pointer_path = ctx.params_latest_pointer_file
    if not pointer_path.exists():
        return None

    try:
        pointer_data = json.loads(pointer_path.read_text(encoding="utf-8"))
        file_name = pointer_data.get("file_name")
        if not isinstance(file_name, str) or not file_name:
            logger.warning("Invalid latest params pointer in %s: missing file_name", pointer_path)
            return None

        candidate_file = ctx.params_output_dir / file_name
        if not candidate_file.exists():
            logger.warning(
                "latest params pointer references missing file '%s' in %s",
                file_name,
                pointer_path,
            )
            return None

        params = cast(ModelParams, joblib.load(candidate_file))
    except Exception as exc:
        logger.warning("Failed loading best params via pointer %s: %s", pointer_path, exc)
        return None

    logger.info("Loaded best params from pointer %s -> %s", pointer_path, candidate_file)
    return params


def load_latest_best_params(ctx: TrainContext) -> ModelParams | None:
    """Load most recent best-params artifact for the selected model if available."""
    pointer_params = _load_best_params_from_pointer(ctx)
    if pointer_params is not None:
        return pointer_params

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
