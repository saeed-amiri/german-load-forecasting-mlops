from pathlib import Path
from types import SimpleNamespace

import duckdb
import pytest

from services.data.ingestion.main import process_source, run_ingestion


def test_process_source_creates_staging_table(tmp_path: Path) -> None:
    csv_path = tmp_path / "input.csv"
    csv_path.write_text("utc_timestamp,value\n2026-01-01 00:00:00,10\n", encoding="utf-8")

    sql_template_path = tmp_path / "staging.sql"
    sql_template_path.write_text(
        "CREATE OR REPLACE TABLE {{ staging_table }} AS SELECT * FROM {{ raw_source_table }};",
        encoding="utf-8",
    )

    ctx = SimpleNamespace(
        source_name="load",
        raw_file=csv_path,
        database=tmp_path / "db.duckdb",
        staging_table="stg_load",
        raw_table="raw_load",
        timestamp_column="utc_timestamp",
        columns=[SimpleNamespace(raw="utc_timestamp", clean="time")],
        sql_template_path=sql_template_path,
    )

    conn = duckdb.connect()
    try:
        process_source(conn, ctx)
        rows = conn.execute("SELECT COUNT(*) FROM stg_load").fetchone()[0]
        assert rows == 1
    finally:
        conn.close()


def test_process_source_wraps_errors(tmp_path: Path) -> None:
    ctx = SimpleNamespace(
        source_name="load",
        raw_file=tmp_path / "missing.csv",
        database=tmp_path / "db.duckdb",
        staging_table="stg_load",
        raw_table="raw_load",
        timestamp_column="utc_timestamp",
        columns=[SimpleNamespace(raw="utc_timestamp", clean="time")],
        sql_template_path=tmp_path / "missing.sql",
    )

    conn = duckdb.connect()
    try:
        with pytest.raises(RuntimeError, match="Processing source 'load' failed"):
            process_source(conn, ctx)
    finally:
        conn.close()


def test_run_ingestion_raises_summary_for_failed_sources(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "ingestion.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.close()

    cfg = SimpleNamespace(
        runtime=SimpleNamespace(),
        logging=SimpleNamespace(level="INFO", to_console=False),
        sql=SimpleNamespace(sources={"ok": object(), "bad": object()}),
        paths=SimpleNamespace(database=db_path),
    )

    monkeypatch.setattr("services.data.ingestion.main.load_config", lambda **_: cfg)
    monkeypatch.setattr("services.data.ingestion.main.resolve_service_log_path", lambda *_: tmp_path / "ingest.log")
    monkeypatch.setattr("services.data.ingestion.main.setup_logging", lambda **_: None)
    monkeypatch.setattr(
        "services.data.ingestion.main.SourceContext.from_config", lambda name, _cfg: SimpleNamespace(source_name=name)
    )

    def fake_process_source(_conn, ctx):
        if ctx.source_name == "bad":
            raise RuntimeError("boom")

    monkeypatch.setattr("services.data.ingestion.main.process_source", fake_process_source)

    with pytest.raises(RuntimeError, match=r"Ingestion failed for sources: \['bad'\]"):
        run_ingestion()
