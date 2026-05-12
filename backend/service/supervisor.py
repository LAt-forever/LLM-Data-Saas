# backend/service/supervisor.py
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from service import crud, db as dbmod, models
from service.config import settings


# Track Popen handles for workers we spawn, so is_pid_alive can detect
# zombie children (POSIX: os.kill(pid, 0) returns success for zombies).
# Without this, a finished worker subprocess is "alive" forever in our view.
_CHILD_PROCS: dict[int, subprocess.Popen] = {}


def _reap_known_child(pid: int) -> bool | None:
    """If pid is one of our tracked children, return True if still running,
    False if it exited (and remove it from the registry). Returns None if
    pid is not a tracked child."""
    proc = _CHILD_PROCS.get(pid)
    if proc is None:
        return None
    rc = proc.poll()
    if rc is None:
        return True
    # Reaped — drop it.
    _CHILD_PROCS.pop(pid, None)
    return False


def spawn_worker(task_id: int, *, mock_llm: bool = False) -> int:
    """Spawn a worker subprocess for the given task. Returns its pid."""
    out_dir = settings.task_dir(task_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-m", "service.worker", "--task-id", str(task_id)]
    if mock_llm:
        cmd.append("--mock-llm")

    log_path = settings.task_log(task_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(log_path, "a", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        stdout=log_fh, stderr=subprocess.STDOUT,
        env={**os.environ,
             "DATA_DIR": str(settings.data_dir),
             "LOG_DIR": str(settings.log_dir),
             "DB_PATH": str(settings.db_path)},
    )
    _CHILD_PROCS[proc.pid] = proc

    # Record pid + output_dir in the task row
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)
    with dbmod.SessionLocal() as s:
        crud.mark_task_started(s, task_id,
                               worker_pid=proc.pid,
                               output_dir=str(out_dir))
    return proc.pid


def is_pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    # If we spawned this pid ourselves, consult the Popen handle so we can
    # tell a running child from an exited-but-not-yet-reaped zombie.
    tracked = _reap_known_child(pid)
    if tracked is not None:
        return tracked
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
    except OSError:
        return False


def terminate_worker(pid: int, *, grace_seconds: int | None = None) -> None:
    if not is_pid_alive(pid):
        return
    grace = grace_seconds if grace_seconds is not None else settings.abort_grace_seconds
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if not is_pid_alive(pid):
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def recover_orphaned_running() -> int:
    """Scan tasks with status='running' whose worker_pid is no longer alive.
    Mark each as failed. Returns how many were recovered."""
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    count = 0
    with dbmod.SessionLocal() as s:
        rows = list(s.query(models.Task).filter_by(status="running").all())
    for row in rows:
        if is_pid_alive(row.worker_pid):
            continue
        with dbmod.SessionLocal() as s:
            crud.mark_task_finished(
                s, row.id, "failed",
                error_msg="service restart, worker lost (orphaned pid)")
            crud.add_task_event(s, row.id, "error",
                                f"worker pid {row.worker_pid} no longer alive")
        count += 1
    return count
