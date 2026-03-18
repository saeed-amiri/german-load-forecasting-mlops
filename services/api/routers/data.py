# services/api/routers/data.py

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from configs.main import PipelineConfig

config = PipelineConfig.load(config_name="config", start_file=Path(__file__))

router = APIRouter()
templates = Jinja2Templates(directory=config.api.templates)


@router.get("/data")
def show_data_dashboard(request: Request):
    fig = _plot_targets()
    plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    table_html = _table_target_overview().to_html()

    return templates.TemplateResponse("data.html", {"request": request, "plot": plot_html, "table": table_html})


def _plot_targets() -> go.Figure:

    with sqlite3.connect(config.paths.database) as conn:
        df = pd.read_sql(f"SELECT * FROM {config.sql.tables.target} ORDER BY time DESC LIMIT 48", conn)

    df_melt = df.melt(
        id_vars=["time"], value_vars=["load_actual", "load_forecast"], var_name="Type", value_name="Load (MW)"
    )
    fig = px.line(df_melt, x="time", y="Load (MW)", color="Type", title="German Electricity Load")

    return fig


def _table_target_overview() -> pd.DataFrame:
    sql = config.api_target_view_sql_path()
    if not sql.exists():
        raise FileNotFoundError(f"Quality check script missing: {sql}")

    with open(sql, "r", encoding="utf8") as f:
        sql_query = f.read()

    with sqlite3.connect(config.paths.database) as conn:
        stats_df = pd.read_sql(sql_query, conn)

    stats_df["peak_load"] = stats_df["peak_load"].astype(str) + " MW"
    stats_df["min_load"] = stats_df["min_load"].astype(str) + " MW"

    # 3. Rename columns for a cleaner look
    stats_df = stats_df.rename(
        columns={
            "day": "Date",
            "peak_load": "Peak Load",
            "peak_time": "Time of Peak",
            "min_load": "Minimum Load",
            "min_time": "Time of Minimum",
        }
    )

    return stats_df
