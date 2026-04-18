"""
MLflow tracking helpers for training runs.
Set uri and mode
"""

import logging
import os
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn

from configs.main import PipelineConfig

from .context import TrainContext

logger = logging.getLogger(__name__)


class MLflowRunManager:
    """Encapsulates MLflow setup and logging for one training run."""

    def __init__(self, cfg: PipelineConfig, ctx: TrainContext):
        self.cfg = cfg
        self.ctx = ctx
        self.enabled = cfg.train.mlflow.enabled
        self._run = None

    def _resolve_tracking_uri(self) -> str:
        configured_uri = self.cfg.train.mlflow.tracking_uri
        env_uri = os.getenv("MLFLOW_TRACKING_URI")
        mode = self.cfg.train.mlflow.tracking_mode

        if env_uri:
            return env_uri

        if configured_uri:
            return configured_uri

        if mode == "local":
            tracking_dir = (self.cfg.paths.models_dir / "mlruns").resolve()
            tracking_dir.mkdir(parents=True, exist_ok=True)
            return tracking_dir.as_uri()

        if mode == "server":
            raise RuntimeError(
                "MLflow tracking_mode='server' requires MLFLOW_TRACKING_URI env var or train.mlflow.tracking_uri config."
            )

        repo = os.getenv("DAGSHUB_REPO") or self.cfg.train.mlflow.dagshub_repo
        if not repo:
            raise RuntimeError(
                "MLflow tracking_mode='dagshub' requires DAGSHUB_REPO env var or train.mlflow.dagshub_repo config."
            )
        return f"https://dagshub.com/{repo}.mlflow"

    def start(self) -> None:
        if not self.enabled:
            return

        tracking_uri = self._resolve_tracking_uri()
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(self.cfg.train.mlflow.experiment_name)

        model_cfg = self.cfg.train.models[self.ctx.model_name]
        model_tag = model_cfg.model_tag or self.ctx.model_name
        run_name = self.cfg.train.mlflow.run_name_template.format(
            model_name=self.ctx.model_name,
            model_tag=model_tag,
            model_id=self.ctx.model_type,
            run_id=self.ctx.run_id,
        )

        self._run = mlflow.start_run(run_name=run_name)
        logger.info("Started MLflow run '%s' on tracking URI %s", run_name, tracking_uri)

    def log_inputs(self) -> None:
        if not self.enabled:
            return

        mlflow.log_params(
            {
                "model_name": self.ctx.model_name,
                "model_type": self.ctx.model_type,
                "train_size": self.ctx.train_size,
                "target_column": self.ctx.target_column,
                "cv_folds": self.ctx.cv_folds,
                "scoring": self.ctx.scoring,
                "feature_count": len(self.ctx.train_columns),
            }
        )

        mlflow.log_param("train_columns", ",".join(self.ctx.train_columns))
        mlflow.log_param("requested_metrics", ",".join(self.ctx.metrics))

        mlflow.set_tags(
            {
                "run_id": self.ctx.run_id,
                "model_output_dir": str(self.ctx.model_output_dir),
                "params_output_dir": str(self.ctx.params_output_dir),
                "tracking_mode": self.cfg.train.mlflow.tracking_mode,
            }
        )

    def log_best_params(self, best_params: dict[str, Any]) -> None:
        if not self.enabled:
            return

        normalized = {f"best__{k}": str(v) for k, v in best_params.items()}
        mlflow.log_params(normalized)

    def log_metrics(self, metrics: dict[str, float]) -> None:
        if not self.enabled:
            return

        mlflow.log_metrics(metrics)

    def log_artifact(self, path: Path, artifact_subdir: str) -> None:
        if not self.enabled or not path.exists():
            return

        mlflow.log_artifact(str(path), artifact_path=artifact_subdir)

    def log_model(self, model: Any) -> None:
        if not self.enabled or not self.cfg.train.mlflow.log_model:
            return

        artifact_path = f"{self.cfg.train.mlflow.artifact_path}/sklearn_model"
        kwargs: dict[str, Any] = {}
        if self.cfg.train.mlflow.register_model:
            kwargs["registered_model_name"] = self.cfg.train.mlflow.registered_model_template.format(
                model_name=self.ctx.model_name,
                model_id=self.ctx.model_type,
            )

        mlflow.sklearn.log_model(sk_model=model, artifact_path=artifact_path, **kwargs)

    def end(self, status: str = "FINISHED") -> None:
        if not self.enabled:
            return

        mlflow.end_run(status=status)
        logger.info("Closed MLflow run with status %s", status)
