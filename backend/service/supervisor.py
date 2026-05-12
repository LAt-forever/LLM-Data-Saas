# backend/service/supervisor.py
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

from service import crud, db as dbmod, models
from service.config import settings


# Track Popen handles for workers we spawn, so is_pid_alive can detect
# zombie children (POSIX: os.kill(pid, 0) returns success for zombies).
# Without this, a finished worker subprocess is "alive" forever in our view.
_LOCK = threading.Lock()
_CHILD_PROCS: dict[int, subprocess.Popen] = {}


def _reap_known_child(pid: int) -> bool | None:
    """If pid is one of our tracked children, return True if still running,
    False if it exited (and remove it from the registry). Returns None if
    pid is not a tracked child."""
    with _LOCK:
        proc = _CHILD_PROCS.get(pid)
    if proc is None:
        return None
    rc = proc.poll()
    if rc is None:
        return True
    # Reaped — drop it.
    with _LOCK:
        _CHILD_PROCS.pop(pid, None)
    return False


def spawn_worker(task_id: int, *, mock_llm: bool = False) -> int | None:
    """Spawn a worker subprocess for the given task.

    Returns the spawned pid on success, or ``None`` if the spawn was
    skipped because the task was already in a terminal state when
    ``mark_task_started`` ran (no-op path). In the skipped case a
    ``warning`` TaskEvent is recorded and no child process is started."""
    out_dir = settings.task_dir(task_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-m", "service.worker", "--task-id", str(task_id)]
    if mock_llm:
        cmd.append("--mock-llm")

    log_path = settings.task_log(task_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Order: mark_task_started BEFORE Popen so the child always sees a
    # populated output_dir (the child reads task.output_dir on startup).
    # Defense-in-depth: mark_task_started silently no-ops if another code
    # path has already marked this task terminal, so we never overwrite
    # terminal status from here.
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)
    with dbmod.SessionLocal() as s:
        task = crud.mark_task_started(s, task_id,
                                      worker_pid=0,
                                      output_dir=str(out_dir))
        if task.status in ("succeeded", "failed", "aborted"):
            # mark_task_started no-op'd because the task is already
            # terminal. Don't spawn an orphan worker against a closed task.
            crud.add_task_event(
                s, task_id, "warning",
                f"spawn_worker skipped: task already {task.status}")
            return None

    with open(log_path, "a", encoding="utf-8") as log_fh:
        proc = subprocess.Popen(
            cmd,
            stdout=log_fh, stderr=subprocess.STDOUT,
            env={**os.environ,
                 "DATA_DIR": str(settings.data_dir),
                 "LOG_DIR": str(settings.log_dir),
                 "DB_PATH": str(settings.db_path)},
        )
    with _LOCK:
        _CHILD_PROCS[proc.pid] = proc

    # Patch in the real pid. Narrow update — does not touch status, so if
    # the child has already reached a terminal state, we don't revert it.
    with dbmod.SessionLocal() as s:
        crud.set_task_worker_pid(s, task_id, proc.pid)
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

    skip_seconds = settings.recover_skip_recent_starting_seconds
    now = datetime.now(timezone.utc)

    for row in rows:
        # Skip rows that are still in the spawn_worker bootstrap window:
        # status=running was just written, but set_task_worker_pid hasn't
        # patched in the real pid yet. Without this guard we'd false-orphan
        # healthy tasks the instant they start. Rows stuck past the window
        # (worker never finished bootstrapping, or crashed before
        # set_task_worker_pid ran) fall through and get marked failed.
        if (row.worker_pid is None) or (row.worker_pid <= 0):
            if row.started_at:
                try:
                    started = datetime.fromisoformat(row.started_at)
                except ValueError:
                    started = None
                if started is not None:
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=timezone.utc)
                    if (now - started).total_seconds() < skip_seconds:
                        continue
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
