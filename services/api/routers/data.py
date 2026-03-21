# services/api/routers/data.py

import logging
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from configs.main import PipelineConfig, load_config

logger = logging.getLogger(__name__)

router = APIRouter()


def get_config():
    """Helper to load config lazily."""
    return load_config(config_name="config", start_file=Path(__file__))


@router.get("/data")
def show_data_dashboard(request: Request):
    config: PipelineConfig = get_config()

    templates = Jinja2Templates(directory=config.api.templates)

    try:
        # Plot uses Features (Hourly Data)
        fig_target = _plot_targets(config)
        plot_target = fig_target.to_html(full_html=False, include_plotlyjs="cdn")
        fig_feature = _plot_featuers(config)
        plot_feature = fig_feature.to_html(full_html=False, include_plotlyjs="cdn")

        # Table uses Marts (Aggregated Stats)
        stats_df = _load_peak_min_data(config)
        table_html = stats_df.to_html(classes="table table-striped", index=False)

        return templates.TemplateResponse(
            "data.html",
            {"request": request, "plot_target": plot_target, "plot_feature": plot_feature, "table": table_html},
        )

    except Exception as e:
        logger.error(f"Failed to generate dashboard: {e}")
        return templates.TemplateResponse(
            "data.html",
            {
                "request": request,
                "plot_target": f"<p class='text-danger'>Error loading plot: {e}</p>",
                "plot_feature": f"<p class='text-danger'>Error loading plot: {e}</p>",
                "table": f"<p class='text-danger'>Error loading data: {e}</p>",
            },
        )


def _plot_targets(config: PipelineConfig) -> go.Figure:
    """
    Reads recent HOURLY data from the FEATURES table to plot the load curve.
    The Marts table is aggregated, so we cannot plot a time-series from it.
    """

    table_name: str = config.sql.tables.marts.load_melt

    with sqlite3.connect(config.paths.database) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))

        if not cursor.fetchone():
            raise RuntimeError(f"Features table '{table_name}' not found. Run preprocessing.")
        df = pd.read_sql_query(
            f"""
            SELECT *
            FROM "{table_name}"
            WHERE time LIKE '2015-01%'
            AND (Type = 'load_actual' OR Type = 'load_forecast')
            ORDER BY time DESC
            """,
            conn,
        )

    fig = px.line(df, x="time", y="Load (MW)", color="Type", title="German Electricity Load")

    return fig


def _plot_featuers(config: PipelineConfig) -> go.Figure:
    """
    plot the features
    """
    table_name: str = config.sql.tables.marts.load_melt

    with sqlite3.connect(config.paths.database) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))

        if not cursor.fetchone():
            raise RuntimeError(f"Features table '{table_name}' not found. Run preprocessing.")
        df = pd.read_sql_query(
            f"""
            SELECT *
            FROM "{table_name}"
            WHERE time LIKE '2015-01%'
            AND (Type ='solar_actual' OR Type ='wind_actual' OR Type ='wind_onshore' OR Type ='wind_offshore')
            ORDER BY time DESC
            """,
            conn,
        )

    fig = px.line(df, x="time", y="Load (MW)", color="Type", title="Features")

    return fig


def _load_peak_min_data(config: PipelineConfig) -> pd.DataFrame:
    """
    Fetches AGGREGATED data from the MARTS table for the dashboard overview table.
    """
    table_name = config.sql.tables.marts.load

    with sqlite3.connect(config.paths.database) as conn:
        # Basic validation
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            return pd.DataFrame()

        df = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT 10', conn)

    if not df.empty:
        if "peak_load" in df.columns:
            df["peak_load"] = df["peak_load"].astype(str) + " MW"
        if "min_load" in df.columns:
            df["min_load"] = df["min_load"].astype(str) + " MW"

        df = df.rename(
            columns={
                "day": "Date",
                "peak_load": "Peak Load",
                "peak_time": "Time of Peak",
                "min_load": "Minimum Load",
                "min_time": "Time of Minimum",
            }
        )

    return df
