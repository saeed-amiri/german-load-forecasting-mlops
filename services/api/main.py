# services/api/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routers import data

app = FastAPI(title="German Load Forecast API")
app.mount("/static", StaticFiles(directory="services/api/static"), name="static")

# Register the router
app.include_router(data.router)

templates = Jinja2Templates(directory="services/api/templates")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
