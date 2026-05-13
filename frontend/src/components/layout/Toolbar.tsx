import { Button, Space, Input } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';

interface FilterItem {
  key: string;
  label: string;
  active?: boolean;
  count?: number;
}

interface ToolbarProps {
  filters?: FilterItem[];
  onFilterChange?: (key: string) => void;
  searchPlaceholder?: string;
  onSearch?: (value: string) => void;
  onCreate?: () => void;
  createLabel?: string;
}

export function Toolbar({
  filters,
  onFilterChange,
  searchPlaceholder,
  onSearch,
  onCreate,
  createLabel = '新建任务',
}: ToolbarProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 16,
        marginBottom: 16,
        flexWrap: 'wrap',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        {filters?.map((f) => (
          <button
            key={f.key}
            onClick={() => onFilterChange?.(f.key)}
            style={{
              padding: '4px 12px',
              borderRadius: 6,
              border: 'none',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              background: f.active ? '#eff6ff' : 'transparent',
              color: f.active ? '#2563eb' : '#64748b',
              transition: 'all 0.15s',
            }}
          >
            {f.label}
            {typeof f.count === 'number' && (
              <span
                style={{
                  marginLeft: 6,
                  fontSize: 11,
                  fontWeight: 600,
                  color: f.active ? '#2563eb' : '#94a3b8',
                }}
              >
                {f.count}
              </span>
            )}
          </button>
        ))}
      </div>

      <Space>
        {onSearch && (
          <Input
            prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
            placeholder={searchPlaceholder}
            onChange={(e) => onSearch(e.target.value)}
            style={{ width: 200 }}
            size="middle"
          />
        )}
        {onCreate && (
          <Button type="primary" icon={<PlusOutlined />} onClick={onCreate}>
            {createLabel}
          </Button>
        )}
      </Space>
    </div>
  );
}
