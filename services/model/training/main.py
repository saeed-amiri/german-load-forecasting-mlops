# services/model/training/main.py

"""
Brain-storm: how to train the data:
steps:
    1- selecotr
    2- save the best parametrs (MLflow)
    3- run the main model
"""

import logging
from pathlib import Path

import pyarrow as pa

from configs.config_logs import resolve_service_log_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

from .context import TrainContext
from .data_io import load_no_nan_data, split_data
from .evaluation import evaluate_regression
from .model_selection import resolve_model_name
from .trainer import train_model
from .tuning import find_best_params

logger = logging.getLogger(__name__)


def run_training(model_name: str | None = None):
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "training")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting Training pipeline execution...")

    selected_model_name = resolve_model_name(config=config, model_name=model_name)
    logger.info("Selected model key for training: %s", selected_model_name)

    ctx: TrainContext = TrainContext.from_config(model_name=selected_model_name, cfg=config)

    arrow_table: pa.Table = load_no_nan_data(ctx)

    X_train, X_test, y_train, y_test = split_data(arrow_table, ctx)

    # 3. Find params
    best_params = find_best_params(X_train, y_train, ctx)

    # 4. Train final model
    model = train_model(X_train, y_train, best_params, ctx)

    # 5. Evaluate
    metrics = evaluate_regression(model, X_test, y_test)
    logger.info("Evaluation metrics: %s", metrics)


if __name__ == "__main__":
    run_training()
