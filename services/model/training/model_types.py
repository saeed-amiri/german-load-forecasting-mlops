"""Shared typing contracts for training models."""

from typing import Protocol, TypeAlias

import pyarrow as pa
from numpy.typing import ArrayLike

ParamValue: TypeAlias = bool | int | float | str | None
ModelParams: TypeAlias = dict[str, ParamValue]
ParamGrid: TypeAlias = dict[str, list[ParamValue]]


class RegressorModel(Protocol):
    """Protocol for estimators used by training/evaluation routines."""

    def fit(self, X: pa.Table, y: pa.Array) -> RegressorModel: ...

    def predict(self, X: pa.Table) -> ArrayLike: ...

    def score(self, X: pa.Table, y: pa.Array) -> float: ...
