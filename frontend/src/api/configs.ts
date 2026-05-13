import { apiGet, apiPost, apiDelete } from './client';
import type {
  ApiConfigOut, ApiConfigCreate, ApiConfigUpdate,
  CategoryOut, CategoryCreate, CategoryUpdate,
  WordListOut, WordListCreate, WordListUpdate,
  PromptTemplateOut, PromptTemplateCreate, PromptTemplateUpdate,
} from './types';

// --- API Configs ---
export function listApiConfigs() {
  return apiGet<ApiConfigOut[]>('/api/api-configs');
}

export function createApiConfig(payload: ApiConfigCreate) {
  return apiPost<ApiConfigOut>('/api/api-configs', payload);
}

export async function updateApiConfig(id: number, payload: ApiConfigUpdate): Promise<ApiConfigOut> {
  const res = await fetch(`/api/api-configs/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'unknown error');
    throw new Error(text);
  }
  return res.json();
}

export function deleteApiConfig(id: number) {
  return apiDelete(`/api/api-configs/${id}`);
}

export function revealApiKey(id: number) {
  return apiGet<{ id: number; api_key: string }>(`/api/api-configs/${id}/reveal`);
}

export function testApiConfig(id: number) {
  return apiPost<{ ok: boolean; latency_ms?: number; sample_text?: string; error?: string }>(`/api/api-configs/${id}/test`, {});
}

// --- WordLists ---
export function listWordlists(kind?: string) {
  const qs = kind ? `?kind=${encodeURIComponent(kind)}` : '';
  return apiGet<WordListOut[]>(`/api/wordlists${qs}`);
}

export function createWordlist(payload: WordListCreate) {
  return apiPost<WordListOut>('/api/wordlists', payload);
}

export async function updateWordlist(id: number, payload: WordListUpdate): Promise<WordListOut> {
  const res = await fetch(`/api/wordlists/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'unknown error');
    throw new Error(text);
  }
  return res.json();
}

export function deleteWordlist(id: number) {
  return apiDelete(`/api/wordlists/${id}`);
}

// --- Prompt Templates ---
export function listPromptTemplates() {
  return apiGet<PromptTemplateOut[]>('/api/prompt-templates');
}

export function createPromptTemplate(payload: PromptTemplateCreate) {
  return apiPost<PromptTemplateOut>('/api/prompt-templates', payload);
}

export async function updatePromptTemplate(id: number, payload: PromptTemplateUpdate): Promise<PromptTemplateOut> {
  const res = await fetch(`/api/prompt-templates/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'unknown error');
    throw new Error(text);
  }
  return res.json();
}

export function deletePromptTemplate(id: number) {
  return apiDelete(`/api/prompt-templates/${id}`);
}

// --- Categories ---
export function listCategories(sample_type?: string) {
  const qs = sample_type ? `?sample_type=${encodeURIComponent(sample_type)}` : '';
  return apiGet<CategoryOut[]>(`/api/categories${qs}`);
}

export function getCategory(id: number) {
  return apiGet<CategoryOut>(`/api/categories/${id}`);
}

export function createCategory(payload: CategoryCreate) {
  return apiPost<CategoryOut>('/api/categories', payload);
}

export async function updateCategory(id: number, payload: CategoryUpdate): Promise<CategoryOut> {
  const res = await fetch(`/api/categories/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'unknown error');
    throw new Error(text);
  }
  return res.json();
}

export function deleteCategory(id: number) {
  return apiDelete(`/api/categories/${id}`);
}
