export const colors = {
  primary: '#181d26',
  primaryHover: '#0d1218',
  primaryActive: '#0d1218',
  primaryBg: '#f5e9d4',

  success: '#0a2e0e',
  successBg: '#e7f0ea',
  warning: '#d9a441',
  warningBg: '#fff7d6',
  error: '#aa2d00',
  errorBg: '#f5e6df',
  info: '#254fad',
  infoBg: '#eef4ff',

  signature: {
    coral: '#aa2d00',
    forest: '#0a2e0e',
    cream: '#f5e9d4',
    peach: '#fcab79',
    mint: '#a8d8c4',
    yellow: '#f4d35e',
    mustard: '#d9a441',
  },

  interaction: {
    focusRing: 'rgba(24,29,38,0.08)',
    sidebarBorder: 'rgba(255,255,255,0.08)',
    sidebarText: 'rgba(255,255,255,0.68)',
    sidebarHoverBg: 'rgba(255,255,255,0.08)',
    sidebarSelectedBg: 'rgba(255,255,255,0.12)',
    progressTrack: '#e0e2e6',
    tableHeader: '#fafafa',
    tableHover: '#fbfaf7',
  },

  text: {
    primary: '#181d26',
    secondary: '#333840',
    tertiary: '#6f737b',
    disabled: '#b8bdc5',
    inverse: '#ffffff',
  },

  border: '#dddddd',
  borderStrong: '#9297a0',
  borderLight: '#ececec',
  bg: '#f8fafc',
  bgElevated: '#ffffff',
  bgSidebar: '#181d26',
  bgSidebarElevated: '#1d1f25',
};

type StatusColor = { dot: string; bg: string; text: string; border?: string };
export type StatusColorKey = 'pending' | 'running' | 'succeeded' | 'failed' | 'aborted';

export const statusColors = {
  pending: { dot: '#9297a0', bg: '#f8fafc', text: '#41454d', border: '#dddddd' },
  running: { dot: '#aa2d00', bg: '#f5e9d4', text: '#181d26', border: '#d8c8aa' },
  succeeded: { dot: '#0a2e0e', bg: '#e7f0ea', text: '#0a2e0e', border: '#b9d3c1' },
  failed: { dot: '#aa2d00', bg: '#f5e6df', text: '#aa2d00', border: '#dfb8a9' },
  aborted: { dot: '#d9a441', bg: '#fff7d6', text: '#6f4f12', border: '#ead58e' },
} satisfies Record<StatusColorKey, StatusColor>;

export const typography = {
  fontFamily: `-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, "Noto Sans", sans-serif`,
  sizes: {
    xs: '12px',
    sm: '13px',
    base: '14px',
    md: '16px',
    lg: '20px',
    xl: '24px',
  },
  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
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
    xs: '2px',
    sm: '4px',
    md: '6px',
    lg: '10px',
    full: '9999px',
  },
};

export const shadow = {
  sm: 'none',
  md: 'none',
  lg: '0 8px 24px rgba(24,29,38,0.08)',
};
