"""
Build training source context from pipeline configuration.

The context resolves per-model training parameters and output locations used
during tuning and final fit stages.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from configs.main import PipelineConfig


@dataclass
class SourceContext:
    """
    Resolved training inputs, hyperparameters, and output paths for one model.
    """

    # main definitions
    model_name: str
    # DatabaseMapping: training dataset
    dataset: Path
    # CommonConfig: main columns
    target_column: str
    train_columns: list[str]
    # EvaluationConfig | ModelEvaluationOverrides: Defaults value | per model
    metrics: list[str]
    cv_folds: int
    scoring: str
    save_predictions: bool
    # ModelTrainingConfig: Model-specific training
    model_type: str
    param_grid: dict[str, list[Any]]
    train_size: float
    # SavedFielConfig: Paths of files to be saved
    ofmt: str
    model_output_dir: Path
    best_params_file: Path
    predictions_file: Path

    @classmethod
    def from_config(cls, model_name: str, cfg: PipelineConfig) -> SourceContext:
        """
        Create training context for a configured model.

        Validates model availability, resolves dataset location from training
        config, and computes model artifact paths.
        :model_name: model name
        """
        model_cfg = cfg.train.models.get(model_name)
        if not model_cfg:
            raise ValueError(f"Model {model_name} not found.")

        if cfg.runtime is None:
            raise RuntimeError("Runtime configuration is not initialized.")

        output_dir = cfg.paths.models_dir
        best_params_file: Path = output_dir / f"{cfg.train.ofiles.best_param_file}.{cfg.train.ofiles.ofmt}"
        predictions_file: Path = output_dir / f"{cfg.train.ofiles.predictions_file}.{cfg.train.ofiles.ofmt}"

        dataset_name = Path(cfg.train.common.database.name)

        if dataset_name.is_absolute():
            dataset = dataset_name
        elif dataset_name.parent == Path("."):
            dataset = cfg.paths.processed_file.with_name(dataset_name.name)
        else:
            dataset = (cfg.project_root / dataset_name).resolve()

        evaluation_override = model_cfg.evaluation_override
        metrics = (
            evaluation_override.metrics
            if evaluation_override and evaluation_override.metrics
            else cfg.train.evaluation.metrics
        )
        cv_folds = (
            evaluation_override.cv_folds
            if evaluation_override and evaluation_override.cv_folds is not None
            else cfg.train.evaluation.cv_folds
        )
        scoring = (
            evaluation_override.scoring
            if evaluation_override and evaluation_override.scoring is not None
            else cfg.train.evaluation.scoring
        )
        save_predictions = (
            evaluation_override.save_predictions
            if evaluation_override and evaluation_override.save_predictions is not None
            else cfg.train.evaluation.save_predictions
        )

        return cls(
            model_name=model_name,
            model_type=model_cfg.type,
            dataset=dataset,
            target_column=cfg.train.common.target_column,
            train_columns=cfg.train.common.train_columns,
            param_grid=model_cfg.param_grid,
            train_size=model_cfg.train_size,
            metrics=metrics,
            cv_folds=cv_folds,
            scoring=scoring,
            save_predictions=save_predictions,
            ofmt=cfg.train.ofiles.ofmt,
            model_output_dir=output_dir,
            best_params_file=best_params_file,
            predictions_file=predictions_file,
        )
