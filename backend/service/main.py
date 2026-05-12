from contextlib import asynccontextmanager

from fastapi import FastAPI

from service import db as dbmod, models  # noqa: F401
from service.config import settings
from service.routers import api_configs as api_configs_router
from service.routers import wordlists as wordlists_router
from service.routers import prompt_templates as prompt_templates_router
from service.routers import categories as categories_router
from service.routers import meta as meta_router
from service.routers import tasks as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)
    # Late import — supervisor depends on engine being initialized.
    from service import supervisor
    supervisor.recover_orphaned_running()
    yield


app = FastAPI(title="LLM Data Service", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_configs_router.router)
app.include_router(wordlists_router.router)
app.include_router(prompt_templates_router.router)
app.include_router(categories_router.router)
app.include_router(meta_router.router)
app.include_router(tasks_router.router)
