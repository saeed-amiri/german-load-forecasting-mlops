# services/api/main.py
import logging
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from configs.main import load_config
from services.data.preprocessing.main import run_transformation

from .routers import data

logger = logging.getLogger(__name__)

app = FastAPI(title="German Load Forecast API")
app.mount("/static", StaticFiles(directory="services/api/static"), name="static")

# Register the router
app.include_router(data.router)

templates = Jinja2Templates(directory="services/api/templates")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.on_event("startup")
def ensure_api_tables() -> None:
    config = load_config(config_name="config", start_file=Path(__file__))
    target_table = config.sql.tables.marts

    with sqlite3.connect(config.paths.database) as conn:
        existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}

    if target_table in existing:
        return

    if "raw_data" not in existing:
        raise RuntimeError(
            f"Missing source table 'raw_data' in {config.paths.database}. "
            "Run the ingestion pipeline before starting the API."
        )

    logger.info("Table '%s' is missing. Building SQL models for API startup.", target_table)
    run_transformation(config)
