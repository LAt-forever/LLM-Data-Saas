from fastapi import FastAPI

from service import db as dbmod, models  # noqa: F401  ensures models import
from service.config import settings

app = FastAPI(title="LLM Data Service", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    settings.ensure_dirs()
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
