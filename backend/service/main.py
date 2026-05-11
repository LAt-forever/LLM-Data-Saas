from fastapi import FastAPI

from service import db as dbmod, models  # noqa: F401
from service.config import settings
from service.routers import api_configs as api_configs_router
from service.routers import wordlists as wordlists_router

app = FastAPI(title="LLM Data Service", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    settings.ensure_dirs()
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_configs_router.router)
app.include_router(wordlists_router.router)
