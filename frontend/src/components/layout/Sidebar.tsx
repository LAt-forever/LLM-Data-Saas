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
  LogoutOutlined,
} from '@ant-design/icons';
import { Link, useLocation } from 'wouter';
import { useAuth } from '../../hooks/useAuth';
import { colors } from '../../theme/tokens';

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
  const { user, logout } = useAuth();

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
        width: collapsed ? 80 : 214,
        minWidth: collapsed ? 80 : 214,
        background: colors.bgSidebar,
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease',
        flexShrink: 0,
        borderRight: `1px solid ${colors.interaction.sidebarBorder}`,
      }}
    >
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: collapsed ? '0 8px' : '0 16px',
          borderBottom: `1px solid ${colors.interaction.sidebarBorder}`,
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 6,
            background: colors.signature.peach,
            boxShadow: `inset 0 -8px 0 ${colors.signature.coral}`,
            flexShrink: 0,
          }}
        />
        {!collapsed && (
          <span
            style={{
              color: colors.text.inverse,
              fontSize: 14,
              fontWeight: 500,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
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
            color: 'rgba(255,255,255,0.58)',
            marginLeft: 'auto',
            padding: 0,
            width: 26,
            height: 26,
          }}
          title={collapsed ? '展开侧边栏' : '收起侧边栏'}
        />
      </div>

      <Menu
        theme="dark"
        mode="inline"
        inlineCollapsed={collapsed}
        selectedKeys={[activeKey]}
        openKeys={collapsed ? [] : openKeys}
        onOpenChange={setOpenKeys}
        style={{
          background: 'transparent',
          borderRight: 'none',
          flex: 1,
          padding: '10px 8px',
          width: '100%',
          boxSizing: 'border-box',
        }}
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

      {user && (
        <div
          style={{
            padding: collapsed ? '14px 18px' : '14px 16px',
            borderTop: `1px solid ${colors.interaction.sidebarBorder}`,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          {!collapsed && (
            <>
              <div
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: '50%',
                  background: colors.bgElevated,
                  color: colors.primary,
                  display: 'grid',
                  placeItems: 'center',
                  fontSize: 11,
                  fontWeight: 500,
                  flexShrink: 0,
                }}
              >
                {(Array.from(user.username.trim())[0] ?? '?').toUpperCase()}
              </div>
              <span
                style={{
                  color: colors.interaction.sidebarText,
                  fontSize: 13,
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {user.username}
              </span>
              <Button
                type="text"
                icon={<LogoutOutlined />}
                onClick={logout}
                style={{ color: 'rgba(255,255,255,0.48)', padding: 0, width: 26, height: 26 }}
                title="退出登录"
              />
            </>
          )}
          {collapsed && (
            <Button
              type="text"
              icon={<LogoutOutlined />}
              onClick={logout}
              style={{ color: 'rgba(255,255,255,0.48)', padding: 0, width: 26, height: 26, margin: '0 auto' }}
              title="退出登录"
            />
          )}
        </div>
      )}
    </aside>
  );
}
