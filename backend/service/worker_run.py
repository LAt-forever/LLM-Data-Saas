# backend/service/worker_run.py
import json
import random
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from service import crud, db as dbmod, models
from service.config import settings
from service.llm_client import LlmClient, AuthError, RetryExhausted
from service.prompt_render import render_prompt
from service.worker_io import CsvVolumeWriter


CSV_HEADER = ["评测题", "风险类型"]
_LINE_PREFIX = re.compile(r"^\s*(?:\d+[\.、]\s*|-\s+)")


def _flush_threshold(batch_size: int) -> int:
    return max(settings.progress_flush_min,
               batch_size * settings.progress_flush_batch_multiplier)


def _parse_lines(text: str) -> list[str]:
    out = []
    for raw in (text or "").splitlines():
        line = _LINE_PREFIX.sub("", raw.strip())
        if len(line) >= 10:
            out.append(line)
    return out


def _mock_call(prompt: str, batch_size: int) -> str:
    return "\n".join(f"{i+1}. mocked line {i+1}" for i in range(batch_size))


def run_task(task_id: int, *, mock_llm: bool = False) -> None:
    """Worker main loop. Reads task by id, runs the generation loop, writes
    CSV volumes, updates progress + events. On error/auth/abort, sets the
    task's terminal status before returning. Never raises.

    Abort semantics (split between worker and supervisor):
      - DB status flip to 'aborted' happens in the tasks router (caller side).
      - This worker checks the task's status at TWO points per round:
          (a) once at the top of each `while` iteration, before submitting
              a new batch of LLM futures;
          (b) once before processing each future's result, so an abort
              requested MID-BATCH stops CSV growth within the current batch
              (not only at the next iteration).
      - In-flight LLM HTTP calls are NOT cancelled by the worker. The
        supervisor sends SIGTERM → abort_grace_seconds → SIGKILL to the
        worker process, which lets the kernel reap any lingering threads.
        Do not try to cancel futures here."""
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    Session = dbmod.SessionLocal
    with Session() as s:
        task = s.get(models.Task, task_id)
        if task is None:
            return
        # If already aborted before worker started, bail without progress.
        if task.status == "aborted":
            crud.add_task_event(s, task_id, "aborted",
                                "worker found task already aborted")
            return
        snapshot_prompt = task.snapshot_prompt_body
        scenario_items = json.loads(task.snapshot_scenario_items_json)
        tone_items = json.loads(task.snapshot_tone_items_json)
        category_name = task.snapshot_category_name
        target_count = task.target_count
        batch_size = task.batch_size
        max_workers = task.max_workers
        max_per_file = task.max_per_file
        output_dir = Path(task.output_dir)

    with Session() as s:
        crud.add_task_event(s, task_id, "started",
                            f"target={target_count} output={output_dir}")

    base_name = f"task_{task_id}"
    writer = CsvVolumeWriter(
        out_dir=output_dir, base_name=base_name,
        header=CSV_HEADER, max_per_file=max_per_file,
    )
    writer.resume()

    # Initial progress from existing rows
    from service.worker_io import count_existing_rows
    current = count_existing_rows(output_dir)
    if current > 0:
        with Session() as s:
            crud.update_task_progress(s, task_id, current)

    flush_thresh = _flush_threshold(batch_size)
    pending_since_flush = 0
    consecutive_batch_failures = 0
    error_terminal_msg: str | None = None
    error_status = "failed"

    def _make_prompt() -> str:
        return render_prompt(snapshot_prompt, {
            "category": category_name,
            "scenario": random.choice(scenario_items) if scenario_items else "",
            "tone": random.choice(tone_items) if tone_items else "",
            "batch_size": str(batch_size),
        })

    def _call_one() -> list[str]:
        prompt = _make_prompt()
        if mock_llm:
            text = _mock_call(prompt, batch_size)
        else:
            client = LlmClient(
                base_url=task_snapshot["base_url"],
                api_key=task_snapshot["api_key"],
                model_name=task_snapshot["model_name"],
                api_type=task_snapshot["api_type"],
            )
            text = client.call(prompt)
        return _parse_lines(text)

    # Read API snapshot once (not via session every batch)
    with Session() as s:
        task = s.get(models.Task, task_id)
        task_snapshot = {
            "base_url": task.snapshot_api_base_url,
            "api_key": task.snapshot_api_key,
            "model_name": task.snapshot_model_name,
            "api_type": task.snapshot_api_type,
        }

    try:
        executor = ThreadPoolExecutor(max_workers=max_workers)
        aborted_mid_run = False
        try:
            while current < target_count:
                # (a) Check abort at the top of each round (before submitting)
                with Session() as s:
                    fresh = s.get(models.Task, task_id)
                    if fresh.status == "aborted":
                        crud.add_task_event(s, task_id, "aborted",
                                            f"aborted at {current}/{target_count}")
                        return

                in_flight_size = min(max_workers, max(1, (target_count - current) // batch_size))
                futures = [executor.submit(_call_one) for _ in range(in_flight_size)]
                batch_added = 0
                for fut in as_completed(futures):
                    try:
                        lines = fut.result()
                    except AuthError as e:
                        error_status = "failed"
                        error_terminal_msg = f"auth error: {e}"[:300]
                        raise
                    except RetryExhausted as e:
                        consecutive_batch_failures += 1
                        with Session() as s:
                            crud.add_task_event(s, task_id, "warning",
                                                f"batch retry exhausted: {e}"[:200])
                        continue
                    consecutive_batch_failures = 0
                    # (b) Check abort before writing each future's rows
                    with Session() as s:
                        fresh = s.get(models.Task, task_id)
                        if fresh.status == "aborted":
                            aborted_mid_run = True
                            crud.add_task_event(s, task_id, "aborted",
                                                f"aborted mid-batch at {current}/{target_count}")
                            break
                    for line in lines:
                        if current >= target_count:
                            break
                        writer.write_row([line, category_name])
                        current += 1
                        batch_added += 1
                        pending_since_flush += 1
                writer.flush()

                if pending_since_flush >= flush_thresh or current >= target_count:
                    with Session() as s:
                        crud.update_task_progress(s, task_id, current)
                        crud.add_task_event(s, task_id, "progress",
                                            f"{current}/{target_count}")
                    pending_since_flush = 0

                if aborted_mid_run:
                    return

                if consecutive_batch_failures >= 10:
                    error_status = "failed"
                    error_terminal_msg = "10 consecutive batch failures, aborting"
                    raise RetryExhausted(error_terminal_msg)
        finally:
            # See docstring: in-flight LLM HTTP calls are not cancelled here;
            # the supervisor sends SIGTERM → SIGKILL to kill the whole process.
            executor.shutdown(wait=False, cancel_futures=True)
            writer.close()

        with Session() as s:
            crud.mark_task_finished(s, task_id, "succeeded")
            crud.add_task_event(s, task_id, "finished",
                                f"generated {current}/{target_count}")
    except AuthError as e:
        with Session() as s:
            crud.mark_task_finished(s, task_id, "failed",
                                    error_msg=error_terminal_msg or str(e)[:300])
            crud.add_task_event(s, task_id, "error",
                                error_terminal_msg or str(e)[:200])
    except RetryExhausted as e:
        with Session() as s:
            crud.mark_task_finished(s, task_id, "failed",
                                    error_msg=error_terminal_msg or str(e)[:300])
            crud.add_task_event(s, task_id, "error",
                                error_terminal_msg or str(e)[:200])
    except Exception as e:
        log_path = settings.task_log(task_id)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        with Session() as s:
            crud.mark_task_finished(s, task_id, "failed",
                                    error_msg=f"{type(e).__name__}: {e}"[:300])
            crud.add_task_event(s, task_id, "error",
                                f"{type(e).__name__}: {e}"[:200])
