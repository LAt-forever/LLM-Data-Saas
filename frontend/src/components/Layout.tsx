import { Layout as AntLayout, Menu } from 'antd';
import { Link, useLocation } from 'wouter';

const { Header, Content } = AntLayout;

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ color: 'white', fontSize: 18, fontWeight: 'bold', marginRight: 32 }}>
          LLM 样本数据服务
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location === '/' ? 'home' : '']}
          items={[
            { key: 'home', label: <Link href="/">任务中心</Link> },
          ]}
          style={{ flex: 1 }}
        />
      </Header>
      <Content style={{ padding: 24, background: '#f0f2f5' }}>
        {children}
      </Content>
    </AntLayout>
  );
}
