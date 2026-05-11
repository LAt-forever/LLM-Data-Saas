import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    log_dir: Path
    db_path: Path
    progress_flush_min: int = 50
    progress_flush_batch_multiplier: int = 5
    max_workers_hard_limit: int = 50
    batch_size_hard_limit: int = 100
    preview_rows: int = 200
    supervisor_poll_seconds: int = 30
    abort_grace_seconds: int = 2

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def task_dir(self, task_id: int) -> Path:
        return self.data_dir / f"task-{task_id}"

    def task_log(self, task_id: int) -> Path:
        return self.log_dir / f"task-{task_id}.log"


def _load() -> Settings:
    return Settings(
        data_dir=Path(os.environ.get("DATA_DIR", "data")).resolve(),
        log_dir=Path(os.environ.get("LOG_DIR", "logs")).resolve(),
        db_path=Path(os.environ.get("DB_PATH", "app.db")).resolve(),
    )


settings = _load()
