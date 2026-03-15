# services/data/preprocessing/main.py
"""
Loading sql script for transfering data into a table
"""

import logging
from pathlib import Path

from core.config import PipelineConfig
from core.log_utils import setup_logging
from .sql_helpers import fetch_sql_script_path, execute_sql_transformation

logger = logging.getLogger(__name__)


def run_transformation() -> None:
    project_root = Path(__file__).resolve().parents[3]

    log_path = project_root / "logs" / "preprocess.log"
    setup_logging(log_file=log_path, level=logging.INFO)

    config = PipelineConfig.load(config_name='config', project_root=project_root)

    try:
        logger.info(f"Connecting to database at {config.paths.database}")
        sql_file_path = fetch_sql_script_path(config, project_root)

        logger.info(f"Executing transformation on {config.paths.database}...")
        count = execute_sql_transformation(config, sql_file_path, logger)

        logger.info(f"SUCCESS: Created '{config.sql.table_name}' with {count} rows.")

    except Exception as err:
        logger.critical("Transformation failed!", exc_info=True)
        raise RuntimeError(f"Transformation Service Failure: {err}") from err


if __name__ == "__main__":
    run_transformation()
