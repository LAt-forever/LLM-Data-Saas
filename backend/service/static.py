# backend/service/static.py
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


def mount_static(app: FastAPI) -> bool:
    """Mount the React dist directory if it exists. Returns whether mounted."""
    static_dir_env = os.environ.get("STATIC_DIR", "frontend/dist")
    dist = Path(static_dir_env).resolve()
    if not (dist.is_dir() and (dist / "index.html").is_file()):
        return False

    index_file = dist / "index.html"

    @app.get("/", include_in_schema=False)
    def _root() -> FileResponse:
        return FileResponse(str(index_file))

    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa_fallback(full_path: str) -> FileResponse:
        # API and healthz paths are matched by their routers first due to
        # route order. This catch-all is a safety net for "stranger" paths
        # and SPA history fallback. Explicitly 404 anything that should
        # have been an API path.
        if full_path.startswith("api/") or full_path.startswith("healthz"):
            raise HTTPException(404)
        candidate = (dist / full_path).resolve()
        if candidate.is_file() and dist in candidate.parents:
            return FileResponse(str(candidate))
        return FileResponse(str(index_file))

    return True
