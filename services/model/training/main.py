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

import time
import joblib
import pyarrow as pa
import adbc_driver_duckdb.dbapi as dbapi
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

from configs.config_logs import resolve_service_log_path
from configs.main import PipelineConfig, load_config
from core.sql_helpers import render_sql_template
from configs.config_sql import sql_script_path
from core.log_utils import setup_logging

from .context import TrainContext

logger = logging.getLogger(__name__)


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


def find_params(X_train: pa.Table, y_train: pa.Table, ctx: TrainContext) -> RandomizedSearchCV:
    """
    Find best parameters for the training and so on
    """
    start_time = time.perf_counter()

    tscv = TimeSeriesSplit(n_splits=ctx.cv_folds)

    base_model = GradientBoostingRegressor()

    searcher = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=ctx.param_grid,
        cv=tscv,
        scoring=ctx.scoring,
        n_jobs=8,
        verbose=1,
    )

    bst_est = searcher.fit(X_train, y_train)
    
    joblib.dump(bst_est, ctx.best_params_file)

    duration = time.perf_counter() - start_time

    logger.info(f"In {duration:.2f} secondes, computed best parameters: {bst_est}, Saved to {ctx.best_params_file}")

    return bst_est


def train_model(X_train, y_train, best_params):
    """
    train data based on the best parameters
    """
    # TODO: Implement the logic for training the data → KAN-10


def evaluate(model, X_test, y_test):
    """
    apply the evaluations test based on the requested one in config
    It may be a whole module of itself!
    """
    # TODO: Implement the evaluations metrics → KAN-10


def run_training():
    config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
    if config.runtime is None:
        raise RuntimeError("Runtime configuration is not initialized.")

    log_path: Path = resolve_service_log_path(config.logging, config.runtime, "training")
    setup_logging(log_file=log_path, level=config.logging.level, to_console=config.logging.to_console)

    logger.info("Starting Training pipeline execution...")

    ctx: TrainContext = TrainContext.from_config(model_name="gbc", cfg=config)

    arrow_table: pa.Table = load_no_nan_data(ctx)

    X_train, X_test, y_train, y_test = split_data(arrow_table, ctx)

    # 3. Find params
    best_params = find_params(X_train, y_train, ctx)

    # 4. Train final model
    # model = train_model(X_train, y_train, best_params)

    # 5. Evaluate
    # evaluate(model, X_test, y_test)


if __name__ == "__main__":
    run_training()
