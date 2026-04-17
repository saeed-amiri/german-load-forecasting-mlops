"""Shared typing contracts for training models."""

from typing import Protocol

import pyarrow as pa
from numpy.typing import ArrayLike


class RegressorModel(Protocol):
    """Protocol for estimators used by training/evaluation routines."""

    def fit(self, X: pa.Table, y: pa.Array) -> RegressorModel: ...

    def predict(self, X: pa.Table) -> ArrayLike: ...

    def score(self, X: pa.Table, y: pa.Array) -> float: ...
