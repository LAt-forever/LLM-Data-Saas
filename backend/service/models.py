from sqlalchemy import (
    Integer, String, Text, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column

from service.db import Base


class ApiConfig(Base):
    __tablename__ = "api_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    base_url: Mapped[str] = mapped_column(String(500))
    api_key: Mapped[str] = mapped_column(String(500))
    model_name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20))  # 'openai' | 'raw'
    created_at: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[str] = mapped_column(String(40), default="")


class WordList(Base):
    __tablename__ = "wordlist"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(40))  # scenario|tone|other
    items_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[str] = mapped_column(String(40), default="")


class PromptTemplate(Base):
    __tablename__ = "prompt_template"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    body: Mapped[str] = mapped_column(Text)
    variables_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[str] = mapped_column(String(40), default="")


class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sample_type: Mapped[str] = mapped_column(String(20))  # black|gray|white
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    prompt_template_id: Mapped[int] = mapped_column(ForeignKey("prompt_template.id"))
    scenario_list_id: Mapped[int] = mapped_column(ForeignKey("wordlist.id"))
    tone_list_id: Mapped[int] = mapped_column(ForeignKey("wordlist.id"))
    default_target_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[str] = mapped_column(String(40), default="")


class Task(Base):
    __tablename__ = "task"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    api_config_id: Mapped[int] = mapped_column(ForeignKey("api_config.id"))

    snapshot_sample_type: Mapped[str] = mapped_column(String(20))
    snapshot_category_name: Mapped[str] = mapped_column(String(300))
    snapshot_prompt_body: Mapped[str] = mapped_column(Text)
    snapshot_scenario_items_json: Mapped[str] = mapped_column(Text)
    snapshot_tone_items_json: Mapped[str] = mapped_column(Text)
    snapshot_api_base_url: Mapped[str] = mapped_column(String(500))
    snapshot_api_key: Mapped[str] = mapped_column(String(500))
    snapshot_model_name: Mapped[str] = mapped_column(String(200))
    snapshot_api_type: Mapped[str] = mapped_column(String(20))

    target_count: Mapped[int] = mapped_column(Integer)
    batch_size: Mapped[int] = mapped_column(Integer)
    max_workers: Mapped[int] = mapped_column(Integer)
    max_per_file: Mapped[int] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(20))  # pending|running|succeeded|failed|aborted
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)

    output_dir: Mapped[str] = mapped_column(String(500))
    worker_pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    resume_from_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("task.id"), nullable=True
    )


Index("ix_task_status", Task.status)
Index("ix_task_created_at", Task.created_at)
Index("ix_task_category_id", Task.category_id)
Index("ix_task_api_config_id", Task.api_config_id)


class TaskEvent(Base):
    __tablename__ = "task_event"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"))
    ts: Mapped[str] = mapped_column(String(40))
    type: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text, default="")


Index("ix_task_event_task_id_id", TaskEvent.task_id, TaskEvent.id)
