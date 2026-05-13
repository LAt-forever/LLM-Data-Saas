import { useState } from 'react';
import { Button, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listCategories, deleteCategory } from '../api/configs';
import { PageShell } from '../components/layout/PageShell';
import { CategoryList } from '../components/settings/CategoryList';
import { CategoryDrawer } from '../components/settings/CategoryDrawer';
import type { CategoryOut } from '../api/types';

export function CategoriesPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<CategoryOut>();
  const queryClient = useQueryClient();

  const { data: categories, isLoading } = useQuery({ queryKey: ['categories'], queryFn: () => listCategories() });

  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => { message.success('已删除'); queryClient.invalidateQueries({ queryKey: ['categories'] }); },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <PageShell title="分类" subtitle="管理样本分类及关联配置"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(undefined); setDrawerOpen(true); }}>新建分类</Button>}
    >
      <CategoryList categories={categories || []} loading={isLoading}
        onEdit={(c) => { setEditing(c); setDrawerOpen(true); }}
        onDelete={(id) => deleteMutation.mutate(id)}
      />
      <CategoryDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} editing={editing} />
    </PageShell>
  );
}
