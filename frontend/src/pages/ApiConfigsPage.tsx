import { useState } from 'react';
import { Button, message, Modal } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listApiConfigs, deleteApiConfig, testApiConfig, revealApiKey } from '../api/configs';
import { PageShell } from '../components/layout/PageShell';
import { ApiConfigList } from '../components/settings/ApiConfigList';
import { ApiConfigDrawer } from '../components/settings/ApiConfigDrawer';
import type { ApiConfigOut } from '../api/types';

export function ApiConfigsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<ApiConfigOut>();
  const queryClient = useQueryClient();

  const { data: configs, isLoading } = useQuery({ queryKey: ['api-configs'], queryFn: listApiConfigs });

  const deleteMutation = useMutation({
    mutationFn: deleteApiConfig,
    onSuccess: () => { message.success('已删除'); queryClient.invalidateQueries({ queryKey: ['api-configs'] }); },
    onError: (err: Error) => message.error(err.message),
  });

  const handleTest = async (id: number) => {
    message.loading({ content: '测试中...', key: `test-${id}` });
    try {
      const res = await testApiConfig(id);
      if (res.ok) message.success({ content: `连通成功 (${res.latency_ms}ms)`, key: `test-${id}` });
      else message.error({ content: `失败: ${res.error}`, key: `test-${id}` });
    } catch (e: any) { message.error({ content: e.message, key: `test-${id}` }); }
  };

  const handleReveal = async (id: number) => {
    try {
      const res = await revealApiKey(id);
      Modal.info({ title: 'API Key', content: <code style={{ wordBreak: 'break-all' }}>{res.api_key}</code> });
    } catch (e: any) { message.error(e.message); }
  };

  return (
    <PageShell title="API 配置" subtitle="管理 LLM 接口连接"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(undefined); setDrawerOpen(true); }}>添加配置</Button>}
    >
      <ApiConfigList configs={configs || []} loading={isLoading}
        onEdit={(c) => { setEditing(c); setDrawerOpen(true); }}
        onDelete={(id) => deleteMutation.mutate(id)}
        onTest={handleTest}
        onReveal={handleReveal}
      />
      <ApiConfigDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} editing={editing} />
    </PageShell>
  );
}
