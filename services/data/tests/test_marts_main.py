from pathlib import Path
from types import SimpleNamespace

import duckdb
import pytest

from services.data.marts.main import _export_table, _process_source, run_marts_pipeline


def test_export_table_delegates_to_shared_export(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def fake_execute_and_export(_conn, sql_query, output_path):
        captured["sql_query"] = sql_query
        captured["output_path"] = output_path
        return 5

    monkeypatch.setattr("services.data.marts.main.execute_and_export", fake_execute_and_export)

    count = _export_table(duckdb.connect(), "tmp_table", tmp_path / "out.parquet")

    assert count == 5
    assert captured["sql_query"] == "SELECT * FROM tmp_table"
    assert captured["output_path"] == tmp_path / "out.parquet"


def test_process_source_executes_main_and_melt(monkeypatch, tmp_path: Path) -> None:
    executed_sql = []
    exported_tables = []

    def fake_render_sql_template(sql_path, context):
        return f"CREATE TABLE {context.get('marts_table', context.get('load_melt'))} AS SELECT 1 AS value"

    def fake_export_table(_conn, table_name, _output_path):
        exported_tables.append(table_name)
        return 1

    class DummyConn:
        def execute(self, sql):
            executed_sql.append(sql)
            return self

    monkeypatch.setattr("services.data.marts.main.render_sql_template", fake_render_sql_template)
    monkeypatch.setattr("services.data.marts.main._export_table", fake_export_table)

    ctx = SimpleNamespace(
        source_name="load",
        sql_path_main=Path("main.sql"),
        sql_path_melt=Path("melt.sql"),
        features_parquet=tmp_path / "features.parquet",
        output_main_parquet=tmp_path / "main.parquet",
        output_melt_parquet=tmp_path / "melt.parquet",
    )

    _process_source(DummyConn(), ctx)

    assert len(executed_sql) == 2
    assert exported_tables == ["tmp_marts_load", "tmp_melt_load"]


def test_run_marts_pipeline_requires_processed_file(monkeypatch, tmp_path: Path) -> None:
    cfg = SimpleNamespace(
        runtime=SimpleNamespace(),
        logging=SimpleNamespace(level="INFO", to_console=False),
        sql=SimpleNamespace(sources={"load": object()}),
        paths=SimpleNamespace(processed_file=tmp_path / "missing.parquet"),
    )

    monkeypatch.setattr("services.data.marts.main.load_config", lambda **_: cfg)
    monkeypatch.setattr("services.data.marts.main.resolve_service_log_path", lambda *_: tmp_path / "marts.log")
    monkeypatch.setattr("services.data.marts.main.setup_logging", lambda **_: None)

    with pytest.raises(FileNotFoundError, match="Run preprocessing first"):
        run_marts_pipeline()
