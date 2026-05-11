from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


ApiType = Literal["openai", "raw"]
SampleType = Literal["black", "gray", "white"]
WordListKind = Literal["scenario", "tone", "other"]
TaskStatus = Literal["pending", "running", "succeeded", "failed", "aborted"]


class ApiConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str = Field(min_length=1, max_length=500)
    model_name: str = Field(min_length=1, max_length=200)
    type: ApiType


class ApiConfigUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    type: ApiType | None = None


class ApiConfigOut(BaseModel):
    id: int
    name: str
    base_url: str
    api_key_masked: str
    model_name: str
    type: ApiType
    created_at: str
    updated_at: str


class WordListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: WordListKind
    items: list[str] = Field(min_length=1)


class WordListUpdate(BaseModel):
    name: str | None = None
    kind: WordListKind | None = None
    items: list[str] | None = None


class WordListOut(BaseModel):
    id: int
    name: str
    kind: WordListKind
    items: list[str]
    created_at: str
    updated_at: str


class PromptTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    variables: list[str]


class PromptTemplateUpdate(BaseModel):
    name: str | None = None
    body: str | None = None
    variables: list[str] | None = None


class PromptTemplateOut(BaseModel):
    id: int
    name: str
    body: str
    variables: list[str]
    created_at: str
    updated_at: str


class CategoryCreate(BaseModel):
    sample_type: SampleType
    name: str = Field(min_length=1, max_length=300)
    description: str = ""
    prompt_template_id: int
    scenario_list_id: int
    tone_list_id: int
    default_target_count: int = Field(ge=0)


class CategoryUpdate(BaseModel):
    sample_type: SampleType | None = None
    name: str | None = None
    description: str | None = None
    prompt_template_id: int | None = None
    scenario_list_id: int | None = None
    tone_list_id: int | None = None
    default_target_count: int | None = None


class CategoryOut(BaseModel):
    id: int
    sample_type: SampleType
    name: str
    description: str
    prompt_template_id: int
    scenario_list_id: int
    tone_list_id: int
    default_target_count: int
    created_at: str
    updated_at: str


class TaskCreate(BaseModel):
    category_id: int
    api_config_id: int
    target_count: int = Field(gt=0)
    batch_size: int = Field(gt=0, le=100)
    max_workers: int = Field(ge=1, le=50)
    max_per_file: int = Field(gt=0)
    created_by_label: str | None = None
    resume_from_task_id: int | None = None


class TaskEventOut(BaseModel):
    id: int
    ts: str
    type: str
    message: str


class TaskOut(BaseModel):
    id: int
    sample_type: SampleType
    category_name: str
    api_config_id: int
    api_model: str
    target_count: int
    batch_size: int
    max_workers: int
    max_per_file: int
    status: TaskStatus
    progress_current: int
    progress_total: int
    created_at: str
    started_at: str | None
    finished_at: str | None
    error_msg: str | None
    output_dir: str
    created_by_label: str | None
    resume_from_task_id: int | None


class TaskDetail(TaskOut):
    snapshot_prompt_body: str
    snapshot_scenario_items: list[str]
    snapshot_tone_items: list[str]
    snapshot_api_base_url: str
    snapshot_api_type: ApiType
    recent_events: list[TaskEventOut]
