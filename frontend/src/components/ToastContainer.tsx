import { message } from 'antd';
import { useEffect } from 'react';
import { useAppStore } from '../store/appStore';

export function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts);
  const removeToast = useAppStore((s) => s.removeToast);

  useEffect(() => {
    toasts.forEach((t) => {
      if (t.type === 'success') message.success(t.message);
      else if (t.type === 'error') message.error(t.message);
      else if (t.type === 'warning') message.warning(t.message);
      else message.info(t.message);
      removeToast(t.id);
    });
  }, [toasts, removeToast]);

  return null;
}
