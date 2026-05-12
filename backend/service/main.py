from contextlib import asynccontextmanager

from fastapi import FastAPI

from service import db as dbmod, models  # noqa: F401
from service.config import settings
from service.routers import api_configs as api_configs_router
from service.routers import wordlists as wordlists_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)
    yield


app = FastAPI(title="LLM Data Service", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_configs_router.router)
app.include_router(wordlists_router.router)
