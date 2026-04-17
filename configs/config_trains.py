# configs/config_trains.py
"""Typed schema for model training configuration."""

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class DatabaseMapping(BaseModel):
    """Reference to the training dataset artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str


class CommonConfig(BaseModel):
    """Global feature/target settings shared by all models."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    database: DatabaseMapping
    target_column: str
    train_columns: list[str] = Field(default_factory=list)


class EvaluationConfig(BaseModel):
    """Evaluation defaults applied to model training."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metrics: list[str] = Field(default_factory=list)
    cv_folds: int = Field(ge=2)
    scoring: str
    save_predictions: bool


class ModelEvaluationOverride(BaseModel):
    """Optional per-model override for evaluation values."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metrics: list[str] = Field(default_factory=list)
    cv_folds: int | None = None
    scoring: str | None = None
    save_predictions: bool | None = None


class ModelTrainingConfig(BaseModel):
    """Model-specific training configuration and hyperparameter grid."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = Field(
        validation_alias=AliasChoices("model_id", "type"),
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    param_grid: dict[str, list[Any]] = Field(default_factory=dict)
    train_size: float = Field(gt=0.0, le=1.0)
    evaluation_override: ModelEvaluationOverride | None = None


class TableNames(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __getattr__(self, item):
        data = self.model_dump()
        try:
            return data[item]
        except KeyError:
            raise AttributeError(item)


class SQLNames(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __getattr__(self, item):
        data = self.model_dump()
        try:
            return data[item]
        except KeyError:
            raise AttributeError(item)


class SqlConfig(BaseModel):
    """File and Table names"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tables: TableNames = Field(default_factory=TableNames)
    files: SQLNames = Field(default_factory=SQLNames)


class SavedFileConfig(BaseModel):
    """Name of the output files"""

    best_params: str
    predictions: str
    ofmt: str


class TrainingConfig(BaseModel):
    """Top-level training configuration loaded from YAML."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    common: CommonConfig
    ofiles: SavedFileConfig
    evaluation: EvaluationConfig
    sql: SqlConfig = Field(default_factory=SqlConfig)
    models: dict[str, ModelTrainingConfig] = Field(default_factory=dict)
