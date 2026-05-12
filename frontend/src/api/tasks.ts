import { apiGet, apiPost, apiDelete } from './client';
import type { TaskOut, TaskDetail, TaskCreatePayload, TaskEventOut, PreviewData, LogData } from './types';

export function listTasks(params?: { status?: string; category_id?: number; page?: number; size?: number }) {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.category_id) search.set('category_id', String(params.category_id));
  if (params?.page) search.set('page', String(params.page));
  if (params?.size) search.set('size', String(params.size));
  const qs = search.toString();
  return apiGet<TaskOut[]>(`/api/tasks${qs ? '?' + qs : ''}`);
}

export function getTask(id: number) {
  return apiGet<TaskDetail>(`/api/tasks/${id}`);
}

export function createTask(payload: TaskCreatePayload) {
  return apiPost<TaskOut>('/api/tasks', payload);
}

export function abortTask(id: number) {
  return apiPost<{ id: number; status: string }>(`/api/tasks/${id}/abort`, {});
}

export function deleteTask(id: number) {
  return apiDelete(`/api/tasks/${id}`);
}

export function previewTask(id: number) {
  return apiGet<PreviewData>(`/api/tasks/${id}/preview`);
}

export function downloadTask(id: number) {
  window.location.href = `/api/tasks/${id}/download`;
}

export function listTaskEvents(id: number, since_id?: number, limit?: number) {
  const search = new URLSearchParams();
  if (since_id !== undefined) search.set('since_id', String(since_id));
  if (limit !== undefined) search.set('limit', String(limit));
  const qs = search.toString();
  return apiGet<TaskEventOut[]>(`/api/tasks/${id}/events${qs ? '?' + qs : ''}`);
}

export function getTaskLog(id: number, lines?: number) {
  const search = new URLSearchParams();
  if (lines !== undefined) search.set('lines', String(lines));
  const qs = search.toString();
  return apiGet<LogData>(`/api/tasks/${id}/log${qs ? '?' + qs : ''}`);
}
