"""Airflow DAG for the end-to-end load forecasting training pipeline."""

from __future__ import annotations

from datetime import datetime

from airflow.models import Variable
from airflow.operators.bash import BashOperator

from airflow import DAG

DEFAULT_ARGS = {
    "owner": "mlops",
    "depends_on_past": False,
    "retries": 1,
}


def _shared_env() -> dict[str, str]:
    """Resolve MLflow and DagsHub env vars from Airflow Variables."""
    return {
        "PYTHONPATH": "/opt/project",
        "MLFLOW_TRACKING_MODE": Variable.get("MLFLOW_TRACKING_MODE", default_var="server"),
        "MLFLOW_TRACKING_URI": Variable.get("MLFLOW_TRACKING_URI", default_var="http://mlflow:5000"),
        "DAGSHUB_REPO": Variable.get("DAGSHUB_REPO", default_var=""),
        "MLFLOW_TRACKING_USERNAME": Variable.get("MLFLOW_TRACKING_USERNAME", default_var=""),
        "MLFLOW_TRACKING_PASSWORD": Variable.get("MLFLOW_TRACKING_PASSWORD", default_var=""),
    }


with DAG(
    dag_id="load_forecast_training_pipeline",
    default_args=DEFAULT_ARGS,
    description="Runs ingestion -> preprocessing -> marts -> training with MLflow tracking",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["load-forecast", "mlops", "mlflow"],
) as dag:
    ingestion = BashOperator(
        task_id="ingestion",
        bash_command="cd /opt/project && python -m services.data.ingestion.main",
        env=_shared_env(),
    )

    preprocessing = BashOperator(
        task_id="preprocessing",
        bash_command="cd /opt/project && python -m services.data.preprocessing.main",
        env=_shared_env(),
    )

    marts = BashOperator(
        task_id="marts",
        bash_command="cd /opt/project && python -m services.data.marts.main",
        env=_shared_env(),
    )

    training = BashOperator(
        task_id="training",
        bash_command="cd /opt/project && python -m services.model.training.main",
        env=_shared_env(),
    )

    ingestion >> preprocessing >> marts >> training
