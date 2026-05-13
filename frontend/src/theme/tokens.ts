export const colors = {
  primary: '#2563eb',
  primaryHover: '#1d4ed8',
  primaryActive: '#1e40af',
  primaryBg: '#eff6ff',

  success: '#10b981',
  successBg: '#ecfdf5',
  warning: '#f59e0b',
  warningBg: '#fffbeb',
  error: '#ef4444',
  errorBg: '#fef2f2',
  info: '#3b82f6',
  infoBg: '#eff6ff',

  text: {
    primary: '#0f172a',
    secondary: '#475569',
    tertiary: '#94a3b8',
    disabled: '#cbd5e1',
  },

  border: '#e2e8f0',
  borderLight: '#f1f5f9',
  bg: '#f8fafc',
  bgElevated: '#ffffff',
  bgSidebar: '#0f172a',
};

export const statusColors: Record<string, { dot: string; bg: string; text: string }> = {
  pending: { dot: '#94a3b8', bg: '#f8fafc', text: '#64748b' },
  running: { dot: '#3b82f6', bg: '#eff6ff', text: '#2563eb' },
  succeeded: { dot: '#10b981', bg: '#ecfdf5', text: '#059669' },
  failed: { dot: '#ef4444', bg: '#fef2f2', text: '#dc2626' },
  aborted: { dot: '#f59e0b', bg: '#fffbeb', text: '#d97706' },
};

export const typography = {
  fontFamily: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji"`,
  sizes: {
    xs: '12px',
    sm: '13px',
    base: '14px',
    md: '16px',
    lg: '20px',
    xl: '24px',
  },
};

export const spacing = {
  unit: 8,
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
};

export const border = {
  radius: {
    sm: '4px',
    md: '6px',
    lg: '8px',
    full: '9999px',
  },
};

export const shadow = {
  sm: '0 1px 2px rgba(0,0,0,0.04)',
  md: '0 1px 3px rgba(0,0,0,0.08)',
  lg: '0 4px 12px rgba(0,0,0,0.08)',
};
