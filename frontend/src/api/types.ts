export type TaskStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'aborted';
export type SampleType = 'black' | 'gray' | 'white';
export type ApiType = 'openai' | 'raw';
export type WordListKind = 'scenario' | 'tone' | 'other';

export interface TaskOut {
  id: number;
  sample_type: SampleType;
  category_name: string;
  api_config_id: number;
  api_model: string;
  target_count: number;
  batch_size: number;
  max_workers: number;
  max_per_file: number;
  status: TaskStatus;
  progress_current: number;
  progress_total: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error_msg: string | null;
  output_dir: string;
  created_by_label: string | null;
  resume_from_task_id: number | null;
}

export interface TaskDetail extends TaskOut {
  snapshot_prompt_body: string;
  snapshot_scenario_items: string[];
  snapshot_tone_items: string[];
  snapshot_api_base_url: string;
  snapshot_api_type: ApiType;
  recent_events: TaskEventOut[];
}

export interface TaskEventOut {
  id: number;
  ts: string;
  type: string;
  message: string;
}

export interface TaskCreatePayload {
  category_id: number;
  api_config_id: number;
  target_count: number;
  batch_size: number;
  max_workers: number;
  max_per_file: number;
  created_by_label?: string;
  resume_from_task_id?: number;
}

export interface CategoryOut {
  id: number;
  sample_type: SampleType;
  name: string;
  description: string;
  prompt_template_id: number;
  scenario_list_id: number;
  tone_list_id: number;
  default_target_count: number;
}

export interface ApiConfigOut {
  id: number;
  name: string;
  base_url: string;
  api_key_masked: string;
  model_name: string;
  type: ApiType;
}

export interface WordListOut {
  id: number;
  name: string;
  kind: WordListKind;
  items: string[];
}

export interface PromptTemplateOut {
  id: number;
  name: string;
  body: string;
  variables: string[];
}

export interface PreviewData {
  header: string[];
  rows: string[][];
}

export interface LogData {
  lines: string[];
}

export interface ApiConfigCreate {
  name: string;
  base_url: string;
  api_key: string;
  model_name: string;
  type: ApiType;
}

export interface ApiConfigUpdate {
  name?: string;
  base_url?: string;
  api_key?: string;
  model_name?: string;
  type?: ApiType;
}

export interface WordListCreate {
  name: string;
  kind: WordListKind;
  items: string[];
}

export interface WordListUpdate {
  name?: string;
  kind?: WordListKind;
  items?: string[];
}

export interface PromptTemplateCreate {
  name: string;
  body: string;
  variables: string[];
}

export interface PromptTemplateUpdate {
  name?: string;
  body?: string;
  variables?: string[];
}

export interface CategoryCreate {
  sample_type: SampleType;
  name: string;
  description?: string;
  prompt_template_id: number;
  scenario_list_id: number;
  tone_list_id: number;
  default_target_count: number;
}

export interface CategoryUpdate {
  sample_type?: SampleType;
  name?: string;
  description?: string;
  prompt_template_id?: number;
  scenario_list_id?: number;
  tone_list_id?: number;
  default_target_count?: number;
}
