from pathlib import Path
from types import SimpleNamespace

import duckdb
import pytest

from services.data.preprocessing.main import process_sources, run_preprocessing, run_transformation


def test_run_transformation_returns_export_count(monkeypatch, tmp_path: Path) -> None:
    calls = {}

    monkeypatch.setattr("services.data.preprocessing.main.render_sql_template", lambda *_args, **_kwargs: "SELECT 1")

    def fake_export(_conn, sql_query, output_path):
        calls["sql_query"] = sql_query
        calls["output_path"] = output_path
        return 7

    monkeypatch.setattr("services.data.preprocessing.main.execute_and_export", fake_export)

    ctx = SimpleNamespace(
        source_name="load", staging_table="stg_load", sql_path_load=Path("load.sql"), output=tmp_path / "out.parquet"
    )

    count = run_transformation(duckdb.connect(), ctx)

    assert count == 7
    assert calls["sql_query"] == "SELECT 1"
    assert calls["output_path"] == tmp_path / "out.parquet"


def test_process_sources_wraps_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.data.preprocessing.main.run_transformation", lambda *_: (_ for _ in ()).throw(ValueError("bad"))
    )

    ctx = SimpleNamespace(source_name="load")

    with pytest.raises(RuntimeError, match="Preprocessing failed for source 'load'"):
        process_sources(duckdb.connect(), ctx)


def test_run_preprocessing_fails_when_database_missing(monkeypatch, tmp_path: Path) -> None:
    cfg = SimpleNamespace(
        runtime=SimpleNamespace(),
        logging=SimpleNamespace(level="INFO", to_console=False),
        sql=SimpleNamespace(sources={"load": object()}),
        paths=SimpleNamespace(database=tmp_path / "missing.duckdb"),
    )

    monkeypatch.setattr("services.data.preprocessing.main.load_config", lambda **_: cfg)
    monkeypatch.setattr(
        "services.data.preprocessing.main.resolve_service_log_path", lambda *_: tmp_path / "preprocess.log"
    )
    monkeypatch.setattr("services.data.preprocessing.main.setup_logging", lambda **_: None)

    with pytest.raises(FileNotFoundError, match="Run ingestion first"):
        run_preprocessing()
