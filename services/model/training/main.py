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
from typing import Any

import adbc_driver_duckdb.dbapi as dbapi
import pyarrow as pa

from configs.config_logs import resolve_service_log_path
from configs.config_sql import sql_script_path
from configs.main import PipelineConfig, load_config
from core.log_utils import setup_logging
from core.sql_helpers import render_sql_template

from .context import TrainContext
from .evaluation import evaluate_regression
from .model_factory import build_model
from .tuning import find_best_params

logger = logging.getLogger(__name__)


def _resolve_model_name(config: PipelineConfig, model_name: str | None = None) -> str:
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


def _check_exist(columns: list[str], cursor: dbapi.Cursor, data: Path) -> None:
    """
    Sanity check: Columns listed in config exists in data file
    """
    cursor.execute(f"DESCRIBE SELECT * FROM read_parquet('{data}')")
    actual_schema = cursor.fetch_arrow_table()
    existing_cols = actual_schema["column_name"].to_pylist()
    missed_cols = []
    for col in columns:
        if col not in existing_cols:
            missed_cols.append(col)
    if missed_cols:
        raise RuntimeError(f"There are missing columns:\n{missed_cols}\nin data source:\n{data}")


def load_no_nan_data(ctx: TrainContext) -> pa.Table:
    """
    load data:
    load the processed file (parquet)
    with sanity check applied to drop NaN rows
    return:
        A pyarrow reader generator batch
    """
    query_file: Path = sql_script_path(ctx.sql.files.load, ctx.sql_dir)

    columns = ctx.train_columns.copy()
    columns.append(ctx.target_column)

    rendered_query = render_sql_template(sql_path=query_file, context={"path": ctx.dataset, "columns": columns})
    with dbapi.connect() as conn:
        with conn.cursor() as cur:
            _check_exist(columns=ctx.train_columns, cursor=cur, data=ctx.dataset)

            cur.execute(rendered_query)

            batch_reader: pa.RecordBatchReader = cur.fetch_record_batch()

            arrow_table = batch_reader.read_all()

    logger.info(f"Data:'{ctx.dataset}' is loaded by SQL script: '{query_file}'")
    return arrow_table


def split_data(arrow_table: pa.Table, ctx: TrainContext) -> tuple[pa.Table, ...]:
    """
    split data, based on the configurations' setup and return in pyarrow tables
    """
    split_index = int(arrow_table.num_rows * ctx.train_size)
    train_table = arrow_table.slice(offset=0, length=split_index)
    test_table = arrow_table.slice(offset=split_index)

    y_train_table = train_table.column(ctx.target_column)
    X_train_table = train_table.select(ctx.train_columns)

    y_test_table = test_table.column(ctx.target_column)
    X_test_table = test_table.select(ctx.train_columns)

    logger.info(f"Train size: {X_train_table.num_rows} | Test size: {X_test_table.num_rows}")

    return X_train_table, X_test_table, y_train_table, y_test_table


def train_model(X_train: pa.Table, y_train: pa.Table, best_params: dict[str, Any], ctx: TrainContext) -> Any:
    """
    train data based on the best parameters
    """
    # TODO: Implement the logic for training the data → KAN-11

    model = build_model(model_id=ctx.model_type, params=best_params)

    model.fit(X_train, y_train)

    return model


def run_training(model_name: str | None = None):
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "training")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting Training pipeline execution...")

    selected_model_name = _resolve_model_name(config=config, model_name=model_name)
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
