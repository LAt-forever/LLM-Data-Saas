import { useState } from 'react';
import { Button, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listWordlists, deleteWordlist } from '../api/configs';
import { PageShell } from '../components/layout/PageShell';
import { WordListList } from '../components/settings/WordListList';
import { WordListDrawer } from '../components/settings/WordListDrawer';
import type { WordListOut } from '../api/types';

export function WordListsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<WordListOut>();
  const queryClient = useQueryClient();

  const { data: wordlists, isLoading } = useQuery({ queryKey: ['wordlists'], queryFn: () => listWordlists() });

  const deleteMutation = useMutation({
    mutationFn: deleteWordlist,
    onSuccess: () => { message.success('已删除'); queryClient.invalidateQueries({ queryKey: ['wordlists'] }); },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <PageShell title="词库" subtitle="管理场景/语气等替换词库"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(undefined); setDrawerOpen(true); }}>新建词库</Button>}
    >
      <WordListList wordlists={wordlists || []} loading={isLoading}
        onEdit={(w) => { setEditing(w); setDrawerOpen(true); }}
        onDelete={(id) => deleteMutation.mutate(id)}
      />
      <WordListDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} editing={editing} />
    </PageShell>
  );
}
