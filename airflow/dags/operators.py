"""
Set Operators for the pipelines
"""

import os

from airflow.operators.bash import BashOperator


class BasePythonOperator(BashOperator):
    """
    Run Python modules directly in the Airflow container.
    Since Airflow already has all dependencies and code mounted,
    we can run Python modules directly without Docker.
    """

    def __init__(
        self,
        task_id: str,
        python_module: str,
        extra_args: str = "",
        cwd: str = "/app",
        **kwargs,
    ):
        command = f"cd {cwd} && python -m {python_module} {extra_args}"

        super().__init__(
            task_id=task_id,
            bash_command=command,
            env={
                **os.environ,
                "PYTHONPATH": "/app",
                "MLFLOW_EXPERIMENT_NAME": os.getenv("MLFLOW_EXPERIMENT_NAME", ""),
                "MLFLOW_TRACKING_MODE": os.getenv("MLFLOW_TRACKING_MODE", "server"),
                "MLFLOW_TRACKING_URI": os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
                "MLFLOW_TRACKING_USERNAME": os.getenv("MLFLOW_TRACKING_USERNAME", ""),
                "MLFLOW_TRACKING_PASSWORD": os.getenv("MLFLOW_TRACKING_PASSWORD", ""),
            },
            cwd=cwd,
            **kwargs,
        )
