from fastapi import FastAPI

from service.config import settings

app = FastAPI(title="LLM Data Service", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    settings.ensure_dirs()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
