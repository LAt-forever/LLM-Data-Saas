import { useState } from 'react';
import { Menu, Button } from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { Link, useLocation } from 'wouter';

const NAV_ITEMS = [
  { key: 'tasks', icon: <DashboardOutlined />, label: '任务中心', href: '/' },
  { key: 'settings', icon: <SettingOutlined />, label: '配置管理', href: '#' },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [location] = useLocation();

  const activeKey = location === '/' ? 'tasks' : '';

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
      {/* Logo */}
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
          <span
            style={{
              color: '#fff',
              fontSize: 15,
              fontWeight: 600,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
            }}
          >
            LLM 样本数据
          </span>
        )}
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setCollapsed(!collapsed)}
          style={{
            color: 'rgba(255,255,255,0.5)',
            marginLeft: 'auto',
            padding: 0,
            width: 24,
            height: 24,
          }}
        />
      </div>

      {/* Nav */}
      <Menu
        theme="dark"
        mode="inline"
        inlineCollapsed={collapsed}
        selectedKeys={[activeKey]}
        style={{
          background: 'transparent',
          borderRight: 'none',
          flex: 1,
          paddingTop: 8,
        }}
        items={NAV_ITEMS.map((item) => ({
          key: item.key,
          icon: item.icon,
          label: item.href === '#' ? (
            <span style={{ color: 'rgba(255,255,255,0.35)' }}>{item.label}</span>
          ) : (
            <Link href={item.href}>{item.label}</Link>
          ),
          disabled: item.href === '#',
        }))}
      />
    </aside>
  );
}
