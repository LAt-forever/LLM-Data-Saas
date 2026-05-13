import { useState } from 'react';
import { Menu, Button } from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  ApiOutlined,
  BookOutlined,
  FileTextOutlined,
  TagsOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { Link, useLocation } from 'wouter';

const NAV_ITEMS = [
  {
    key: 'tasks',
    icon: <DashboardOutlined />,
    label: '任务中心',
    href: '/',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '配置管理',
    children: [
      { key: 'api-configs', icon: <ApiOutlined />, label: 'API 配置', href: '/settings/api-configs' },
      { key: 'wordlists', icon: <BookOutlined />, label: '词库', href: '/settings/wordlists' },
      { key: 'prompt-templates', icon: <FileTextOutlined />, label: 'Prompt 模板', href: '/settings/prompt-templates' },
      { key: 'categories', icon: <TagsOutlined />, label: '分类', href: '/settings/categories' },
    ],
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [location] = useLocation();
  const [openKeys, setOpenKeys] = useState<string[]>(['settings']);

  const activeKey = (() => {
    if (location === '/') return 'tasks';
    if (location.startsWith('/settings/api-configs')) return 'api-configs';
    if (location.startsWith('/settings/wordlists')) return 'wordlists';
    if (location.startsWith('/settings/prompt-templates')) return 'prompt-templates';
    if (location.startsWith('/settings/categories')) return 'categories';
    return '';
  })();

  return (
    <aside
      style={{
        width: collapsed ? 64 : 200,
        minWidth: collapsed ? 64 : 200,
        background: '#0f172a',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s',
        flexShrink: 0,
      }}
    >
      <div
        style={{
          height: 48,
          display: 'flex',
          alignItems: 'center',
          padding: collapsed ? '0 20px' : '0 16px',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        {!collapsed && (
          <span style={{ color: '#fff', fontSize: 15, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden' }}>
            LLM 样本数据
          </span>
        )}
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setCollapsed(!collapsed)}
          style={{ color: 'rgba(255,255,255,0.5)', marginLeft: 'auto', padding: 0, width: 24, height: 24 }}
        />
      </div>

      <Menu
        theme="dark"
        mode="inline"
        inlineCollapsed={collapsed}
        selectedKeys={[activeKey]}
        openKeys={collapsed ? [] : openKeys}
        onOpenChange={setOpenKeys}
        style={{ background: 'transparent', borderRight: 'none', flex: 1, paddingTop: 8 }}
        items={NAV_ITEMS.map((item) => {
          if (item.children) {
            return {
              key: item.key,
              icon: item.icon,
              label: item.label,
              children: item.children.map((c) => ({
                key: c.key,
                icon: c.icon,
                label: <Link href={c.href}>{c.label}</Link>,
              })),
            };
          }
          return {
            key: item.key,
            icon: item.icon,
            label: <Link href={item.href!}>{item.label}</Link>,
          };
        })}
      />
    </aside>
  );
}
