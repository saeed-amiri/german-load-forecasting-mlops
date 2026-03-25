# services/api/main.py
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from configs.main import PipelineConfig, load_config

from .context import APIContext
from .routers import data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


config: PipelineConfig = load_config(config_name="config", start_file=Path(__file__))
api_ctx: APIContext = APIContext.from_config(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_data_state(api_ctx)
    yield


def verify_data_state(ctx: APIContext) -> None:
    """Verifies that required marts parquet files exist."""
    try:
        missing = [str(path) for path in (ctx.marts_main_parquet, ctx.marts_melt_parquet) if not path.exists()]

        if missing:
            logger.warning(
                "API startup checks failed. Missing marts outputs: %s. Run ingestion -> preprocessing -> marts.",
                missing,
            )
        else:
            logger.info("API startup checks passed for source '%s'.", ctx.source_name)

    except Exception as e:
        logger.error(f"Failed to verify data state on startup: {e}")


app = FastAPI(title="German Load Forecast API", lifespan=lifespan)

app.state.config = config
app.state.api_ctx = api_ctx

app.mount("/static", StaticFiles(directory=str(api_ctx.static_dir)), name="static")


app.include_router(data.router)

templates = Jinja2Templates(directory=str(api_ctx.templates_dir))


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
