import type { ThemeConfig } from 'antd';

export const antdTheme: ThemeConfig = {
  token: {
    colorPrimary: '#2563eb',
    colorSuccess: '#10b981',
    colorWarning: '#f59e0b',
    colorError: '#ef4444',
    colorInfo: '#3b82f6',
    borderRadius: 6,
    borderRadiusSM: 4,
    borderRadiusLG: 8,
    fontSize: 14,
    fontSizeSM: 13,
    fontSizeLG: 16,
    controlHeight: 32,
    controlHeightSM: 28,
    controlHeightLG: 40,
    paddingContentHorizontal: 16,
    paddingContentVertical: 12,
    colorText: '#0f172a',
    colorTextSecondary: '#475569',
    colorTextTertiary: '#94a3b8',
    colorBorder: '#e2e8f0',
    colorBorderSecondary: '#f1f5f9',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f8fafc',
  },
  components: {
    Table: {
      borderRadius: 6,
      padding: 12,
      paddingXS: 8,
      paddingSM: 8,
      fontSize: 13,
      fontSizeSM: 12,
    },
    Card: {
      borderRadius: 8,
      paddingLG: 20,
    },
    Button: {
      borderRadius: 6,
      paddingInline: 16,
    },
    Tag: {
      borderRadius: 4,
      fontSize: 12,
      lineHeight: 1.5,
    },
    Menu: {
      iconSize: 18,
      iconMarginInlineEnd: 12,
    },
    Drawer: {
      borderRadius: 0,
      paddingLG: 24,
    },
    Tabs: {
      borderRadius: 6,
      margin: 0,
    },
    Progress: {
      borderRadius: 4,
    },
  },
};
