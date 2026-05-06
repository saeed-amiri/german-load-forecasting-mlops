# airflow/dags/load_forecast_training_pipeline.py
"""
Airflow DAG for the end-to-end load forecasting training pipeline.
"""

from __future__ import annotations

import pendulum
from operators import BasePythonOperator

from airflow import DAG

DEFAULT_ARGS = {
    "owner": "mlops",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="load_forecast_training_pipeline",
    default_args=DEFAULT_ARGS,
    description="Runs ingestion -> preprocessing -> marts -> training with MLflow tracking",
    start_date=pendulum.datetime(2026, 4, 19, tz="UTC"),
    schedule=None,  # Manual trigger
    catchup=False,
    max_active_runs=1,
    tags=["load-forecast", "mlops", "mlflow"],
) as dag:
    ingestion = BasePythonOperator(
        task_id="ingestion",
        python_module="services.data.ingestion.main",
    )

    preprocessing = BasePythonOperator(
        task_id="preprocessing",
        python_module="services.data.preprocessing.main",
    )

    marts = BasePythonOperator(
        task_id="marts",
        python_module="services.data.marts.main",
    )

    training = BasePythonOperator(
        task_id="training",
        python_module="services.model.training.main",
    )

    # Clean, linear data-science pipeline. No DVC clutter.
    ingestion >> preprocessing >> marts >> training
