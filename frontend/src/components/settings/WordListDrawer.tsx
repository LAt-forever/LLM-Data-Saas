import { Drawer, Form, Input, Select, Button, message } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createWordlist, updateWordlist } from '../../api/configs';
import type { WordListCreate, WordListOut, WordListKind } from '../../api/types';

interface Props { open: boolean; onClose: () => void; editing?: WordListOut; }

export function WordListDrawer({ open, onClose, editing }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!editing;

  const mutation = useMutation({
    mutationFn: (values: WordListCreate) =>
      isEdit ? updateWordlist(editing!.id, values) : createWordlist(values),
    onSuccess: () => {
      message.success(isEdit ? '已更新' : '已创建');
      queryClient.invalidateQueries({ queryKey: ['wordlists'] });
      onClose();
    },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Drawer title={isEdit ? '编辑词库' : '新建词库'} placement="right" size="large" style={{ width: 480 }} open={open} onClose={onClose} destroyOnClose
      footer={<div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><Button onClick={onClose}>取消</Button><Button type="primary" loading={mutation.isPending} onClick={() => form.submit()}>保存</Button></div>}
    >
      <Form form={form} layout="vertical" onFinish={(v) => {
        const values = v as { name: string; kind: string; items: string };
        mutation.mutate({
          name: values.name,
          kind: values.kind as WordListKind,
          items: values.items.split('\n').map((s) => s.trim()).filter(Boolean),
        });
      }}
        initialValues={editing ? { ...editing, items: editing.items.join('\n') } : { kind: 'scenario' }}
      >
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="kind" label="类型" rules={[{ required: true }]}>
          <Select options={[{ value: 'scenario', label: '场景' }, { value: 'tone', label: '语气' }, { value: 'other', label: '其他' }]} />
        </Form.Item>
        <Form.Item name="items" label="词库内容" rules={[{ required: true }]} extra="每行一个词">
          <Input.TextArea rows={12} placeholder="shopping&#10;travel&#10;coding" />
        </Form.Item>
      </Form>
    </Drawer>
  );
}
