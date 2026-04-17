"""Data loading and splitting helpers for model training."""

import logging
from pathlib import Path

import adbc_driver_duckdb.dbapi as dbapi
import pyarrow as pa

from configs.config_sql import sql_script_path
from core.sql_helpers import render_sql_template

from .context import TrainContext

logger = logging.getLogger(__name__)


def _check_exist(columns: list[str], cursor: dbapi.Cursor, data: Path) -> None:
    """Validate that configured feature columns exist in the source parquet."""
    cursor.execute(f"DESCRIBE SELECT * FROM read_parquet('{data}')")
    actual_schema = cursor.fetch_arrow_table()
    existing_cols = actual_schema["column_name"].to_pylist()

    missed_cols = [col for col in columns if col not in existing_cols]
    if missed_cols:
        raise RuntimeError(f"Missing configured columns {missed_cols} in data source '{data}'.")


def load_no_nan_data(ctx: TrainContext) -> pa.Table:
    """Load training data via SQL template and return a materialized Arrow table."""
    query_file: Path = sql_script_path(ctx.sql.files.load, ctx.sql_dir)

    columns = [*ctx.train_columns, ctx.target_column]
    rendered_query = render_sql_template(sql_path=query_file, context={"path": ctx.dataset, "columns": columns})

    with dbapi.connect() as conn:
        with conn.cursor() as cur:
            _check_exist(columns=ctx.train_columns, cursor=cur, data=ctx.dataset)
            cur.execute(rendered_query)
            batch_reader: pa.RecordBatchReader = cur.fetch_record_batch()
            arrow_table = batch_reader.read_all()

    logger.info("Data '%s' loaded using SQL script '%s'", ctx.dataset, query_file)
    return arrow_table


def split_data(arrow_table: pa.Table, ctx: TrainContext) -> tuple[pa.Table, pa.Table, pa.Array, pa.Array]:
    """Split Arrow table into train/test features and targets according to configured train_size."""
    split_index = int(arrow_table.num_rows * ctx.train_size)

    train_table = arrow_table.slice(offset=0, length=split_index)
    test_table = arrow_table.slice(offset=split_index)

    y_train = train_table.column(ctx.target_column)
    x_train = train_table.select(ctx.train_columns)
    y_test = test_table.column(ctx.target_column)
    x_test = test_table.select(ctx.train_columns)

    logger.info("Train size: %s | Test size: %s", x_train.num_rows, x_test.num_rows)
    return x_train, x_test, y_train, y_test
