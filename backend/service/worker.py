# backend/service/worker.py
"""CLI entry: python -m service.worker --task-id N [--mock-llm]"""
import argparse

from service import db as dbmod
from service.worker_run import run_task


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument("--mock-llm", action="store_true",
                        help="Skip real LLM calls; emit synthetic batches.")
    args = parser.parse_args()

    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    run_task(args.task_id, mock_llm=args.mock_llm)


if __name__ == "__main__":
    main()
