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

import joblib
import pyarrow as pa
from mlflow.exceptions import MlflowException

from configs.config_logs import resolve_service_log_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging

from .best_params import resolve_best_params
from .context import TrainContext
from .data_io import load_no_nan_data, split_data
from .evaluation import evaluate_regression
from .mlflow_tracking import MLflowRunManager
from .model_selection import resolve_model_name
from .trainer import train_model

logger = logging.getLogger(__name__)


def run_training(model_name: str | None = None, use_saved_best_params: bool | None = None) -> None:
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "training")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting Training pipeline execution...")

    selected_model_name = resolve_model_name(config=config, model_name=model_name)
    logger.info("Selected model key for training: %s", selected_model_name)

    ctx: TrainContext = TrainContext.from_config(model_name=selected_model_name, cfg=config)
    mlflow_run = MLflowRunManager(cfg=config, ctx=ctx)

    try:
        mlflow_run.start()
        mlflow_run.log_inputs()

        arrow_table: pa.Table = load_no_nan_data(ctx)

        X_train, X_test, y_train, y_test = split_data(arrow_table, ctx)

        reuse_params = config.train.use_saved_best_params if use_saved_best_params is None else use_saved_best_params
        logger.info("Best-params strategy: %s", "reuse_saved_or_search" if reuse_params else "search")

        # 3. Resolve best params (load saved if requested; otherwise search)
        best_params = resolve_best_params(X_train, y_train, ctx, use_saved_best_params=reuse_params)
        mlflow_run.log_best_params(best_params)

        # 4. Train final model
        model = train_model(X_train, y_train, best_params, ctx)
        joblib.dump(model, ctx.model_file)
        logger.info("Saved trained model to %s", ctx.model_file)
        logger.info("Best params stored at %s", ctx.best_params_file)

        # 5. Evaluate
        metrics = evaluate_regression(model, X_test, y_test)
        logger.info("Evaluation metrics: %s", metrics)
        mlflow_run.log_metrics(metrics)
        mlflow_run.log_artifact(ctx.best_params_file, f"{config.train.mlflow.artifact_path}/best_params")
        mlflow_run.log_artifact(ctx.model_file, f"{config.train.mlflow.artifact_path}/artifacts")
        mlflow_run.log_model(model)
        mlflow_run.end(status="FINISHED")
    except MlflowException as err:
        mlflow_run.end(status="FAILED")
        raise RuntimeError("Failed to run MLFlow") from err


if __name__ == "__main__":
    run_training()
