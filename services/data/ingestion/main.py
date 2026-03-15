# services/data/ingestion/main.py
"""
Ingestion of the raw data

The raw data transforms to a sql database by pandas
"""

import logging
from pathlib import Path

import pandas as pd

from core.config import PipelineConfig
from core.log_utils import setup_logging

from .io_helpers import load_raw_data, save_to_sqlite


logger = logging.getLogger(__name__)


def run_ingestion():
    """
    Main entry point for the data ingestion pipeline.
    Orchestrates configuration loading, logging, and data transfer.
    """
    project_root = Path(__file__).resolve().parents[3]

    log_path = project_root / "logs" / "ingest.log"
    setup_logging(log_file=log_path, level=logging.INFO)

    logger.info("Starting ingestion-pipeline execution...")

    config = PipelineConfig.load(config_name='config', project_root=project_root)

    try:
        df = load_raw_data(config, logger)

        df['ingested_at'] = pd.Timestamp.now()

        save_to_sqlite(df=df, config=config, logger=logger)

        logger.info(f"Pipeline finished successfully. Processed {len(df)} rows.")

    except Exception as e:
        logger.critical(f"Pipeline failed (Ingestion) {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    run_ingestion()
