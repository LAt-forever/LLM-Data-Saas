import { useState } from 'react';
import { Button, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listPromptTemplates, deletePromptTemplate } from '../api/configs';
import { PageShell } from '../components/layout/PageShell';
import { PromptTemplateList } from '../components/settings/PromptTemplateList';
import { PromptTemplateDrawer } from '../components/settings/PromptTemplateDrawer';
import type { PromptTemplateOut } from '../api/types';

export function PromptTemplatesPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<PromptTemplateOut>();
  const queryClient = useQueryClient();

  const { data: templates, isLoading } = useQuery({ queryKey: ['prompt-templates'], queryFn: listPromptTemplates });

  const deleteMutation = useMutation({
    mutationFn: deletePromptTemplate,
    onSuccess: () => { message.success('已删除'); queryClient.invalidateQueries({ queryKey: ['prompt-templates'] }); },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <PageShell title="Prompt 模板" subtitle="管理样本生成 Prompt 模板"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(undefined); setDrawerOpen(true); }}>新建模板</Button>}
    >
      <PromptTemplateList templates={templates || []} loading={isLoading}
        onEdit={(t) => { setEditing(t); setDrawerOpen(true); }}
        onDelete={(id) => deleteMutation.mutate(id)}
      />
      <PromptTemplateDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} editing={editing} />
    </PageShell>
  );
}
