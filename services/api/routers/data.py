# services/api/routers/data.py

import logging
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from configs.main import PipelineConfig, load_config
from services.api.context import APIContext

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_runtime_context(request: Request) -> tuple[PipelineConfig, APIContext]:
    config = getattr(request.app.state, "config", None)
    api_ctx = getattr(request.app.state, "api_ctx", None)

    if config is None or api_ctx is None:
        config = load_config(config_name="config", start_file=Path(__file__))
        api_ctx = APIContext.from_config(config)

    return config, api_ctx


@router.get("/data")
def show_data_dashboard(request: Request):
    _, api_ctx = _get_runtime_context(request)

    templates = Jinja2Templates(directory=str(api_ctx.templates_dir))

    try:
        # Plot uses Features (Hourly Data)
        fig_target = _plot_targets(api_ctx)
        plot_target = fig_target.to_html(full_html=False, include_plotlyjs="cdn")
        fig_feature = _plot_features(api_ctx)
        plot_feature = fig_feature.to_html(full_html=False, include_plotlyjs="cdn")

        # Table uses Marts (Aggregated Stats)
        stats_df = _load_peak_min_data(api_ctx)
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


def _plot_targets(ctx: APIContext) -> go.Figure:
    """
    Reads recent HOURLY data from the FEATURES table to plot the load curve.
    The Marts table is aggregated, so we cannot plot a time-series from it.
    """

    if not ctx.marts_melt_parquet.exists():
        raise RuntimeError(f"Marts melt parquet '{ctx.marts_melt_parquet}' not found. Run marts.")

    with duckdb.connect() as conn:
        df = conn.execute(
            f"""
            SELECT *
            FROM '{ctx.marts_melt_parquet}'
            WHERE strftime(time, '%Y-%m') = '2015-01'
              AND Type IN ('load_actual', 'load_forecast')
            ORDER BY time DESC
            """
        ).fetchdf()

    fig = px.line(df, x="time", y="Load (MW)", color="Type", title="German Electricity Load")

    return fig


def _plot_features(ctx: APIContext) -> go.Figure:
    """
    plot the features
    """
    if not ctx.marts_melt_parquet.exists():
        raise RuntimeError(f"Marts melt parquet '{ctx.marts_melt_parquet}' not found. Run marts.")

    with duckdb.connect() as conn:
        df = conn.execute(
            f"""
            SELECT *
            FROM '{ctx.marts_melt_parquet}'
            WHERE strftime(time, '%Y-%m') = '2015-01'
              AND Type IN ('solar_actual', 'wind_actual', 'wind_onshore', 'wind_offshore')
            ORDER BY time DESC
            """
        ).fetchdf()

    fig = px.line(df, x="time", y="Load (MW)", color="Type", title="Features")

    return fig


def _load_peak_min_data(ctx: APIContext) -> pd.DataFrame:
    """
    Fetches AGGREGATED data from the MARTS table for the dashboard overview table.
    """
    if not ctx.marts_main_parquet.exists():
        return pd.DataFrame()

    with duckdb.connect() as conn:
        df = conn.execute(f"SELECT * FROM '{ctx.marts_main_parquet}' LIMIT 10").fetchdf()

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
