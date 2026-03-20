# services/api/main.py
import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from configs import PipelineConfig
from configs.main import load_config

from .routers import data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_database_state()
    yield


def verify_database_state() -> None:
    """
    Verifies that the required database tables exist.
    """
    try:
        config = load_config(config_name="config", start_file=Path(__file__))
        target_table = config.sql.tables.marts.load

        with sqlite3.connect(config.paths.database) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (target_table,))
            exists = cursor.fetchone()

        if not exists:
            logger.warning(
                f"API Table '{target_table}' not found in database. "
                "Please run the pipeline services (ingestion -> preprocessing -> marts)."
            )
        else:
            logger.info(f"API Startup check passed. Table '{target_table}' found.")

    except Exception as e:
        logger.error(f"Failed to verify database state on startup: {e}")


app = FastAPI(title="German Load Forecast API", lifespan=lifespan)


config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))

app.mount("/static", StaticFiles(directory=config.api.static), name="static")


app.include_router(data.router)

templates = Jinja2Templates(directory=config.api.templates)


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
