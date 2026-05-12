import { create } from 'zustand';

export type SseState = 'connecting' | 'connected' | 'reconnecting' | 'closed';

export interface ToastItem {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
}

interface AppState {
  sseStates: Record<number, SseState>;
  setSseState: (taskId: number, state: SseState) => void;
  toasts: ToastItem[];
  addToast: (toast: Omit<ToastItem, 'id'>) => void;
  removeToast: (id: string) => void;
}

let toastIdCounter = 0;

export const useAppStore = create<AppState>((set) => ({
  sseStates: {},
  setSseState: (taskId, state) =>
    set((s) => ({
      sseStates: { ...s.sseStates, [taskId]: state },
    })),
  toasts: [],
  addToast: (toast) =>
    set((s) => ({
      toasts: [...s.toasts, { ...toast, id: `toast-${++toastIdCounter}` }],
    })),
  removeToast: (id) =>
    set((s) => ({
      toasts: s.toasts.filter((t) => t.id !== id),
    })),
}));
