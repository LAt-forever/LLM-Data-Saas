import { Card } from 'antd';

interface DetailSectionProps {
  title: string;
  icon?: React.ReactNode;
  extra?: React.ReactNode;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export function DetailSection({ title, icon, extra, children, style }: DetailSectionProps) {
  return (
    <Card
      style={{
        borderRadius: 8,
        ...style,
      }}
      title={
        <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600 }}>
          {icon}
          {title}
        </span>
      }
      extra={extra}
      bodyStyle={{ padding: 20 }}
    >
      {children}
    </Card>
  );
}
