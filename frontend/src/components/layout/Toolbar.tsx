import { Button, Space, Input } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { colors } from '../../theme/tokens';

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

const ACTIVE_FILTER_BORDER = '#d8c8aa';

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
        gap: 14,
        marginBottom: 16,
        flexWrap: 'wrap',
        minWidth: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', minWidth: 0 }}>
        {filters?.map((f) => (
          <button
            type="button"
            key={f.key}
            aria-pressed={!!f.active}
            onClick={() => onFilterChange?.(f.key)}
            style={{
              height: 32,
              padding: '0 12px',
              borderRadius: 8,
              border: f.active ? `1px solid ${ACTIVE_FILTER_BORDER}` : '1px solid transparent',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              background: f.active ? colors.primaryBg : 'transparent',
              color: f.active ? colors.text.primary : colors.text.secondary,
              transition: 'background 160ms ease, border-color 160ms ease, color 160ms ease',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              whiteSpace: 'nowrap',
            }}
          >
            {f.label}
            {typeof f.count === 'number' && (
              <span style={{ fontSize: 11, fontWeight: 500, color: colors.text.tertiary }}>{f.count}</span>
            )}
          </button>
        ))}
      </div>

      <Space wrap>
        {onSearch && (
          <Input
            prefix={<SearchOutlined style={{ color: colors.text.tertiary }} />}
            placeholder={searchPlaceholder}
            onChange={(e) => onSearch(e.target.value)}
            style={{ width: 220 }}
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
