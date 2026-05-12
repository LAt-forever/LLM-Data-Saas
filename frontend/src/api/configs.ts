import { apiGet } from './client';
import type { ApiConfigOut, CategoryOut, WordListOut, PromptTemplateOut } from './types';

export function listApiConfigs() {
  return apiGet<ApiConfigOut[]>('/api/api-configs');
}

export function listCategories(sample_type?: string) {
  const qs = sample_type ? `?sample_type=${encodeURIComponent(sample_type)}` : '';
  return apiGet<CategoryOut[]>(`/api/categories${qs}`);
}

export function listWordlists(kind?: string) {
  const qs = kind ? `?kind=${encodeURIComponent(kind)}` : '';
  return apiGet<WordListOut[]>(`/api/wordlists${qs}`);
}

export function listPromptTemplates() {
  return apiGet<PromptTemplateOut[]>('/api/prompt-templates');
}
