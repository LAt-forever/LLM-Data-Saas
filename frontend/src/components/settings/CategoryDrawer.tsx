import { Drawer, Form, Input, InputNumber, Select, Button, message } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createCategory, updateCategory, listWordlists, listPromptTemplates } from '../../api/configs';
import type { CategoryCreate, CategoryOut } from '../../api/types';

interface Props { open: boolean; onClose: () => void; editing?: CategoryOut; }

export function CategoryDrawer({ open, onClose, editing }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!editing;

  const { data: wordlists } = useQuery({ queryKey: ['wordlists'], queryFn: () => listWordlists(), enabled: open });
  const { data: templates } = useQuery({ queryKey: ['prompt-templates'], queryFn: () => listPromptTemplates(), enabled: open });

  const mutation = useMutation({
    mutationFn: (values: CategoryCreate) =>
      isEdit ? updateCategory(editing!.id, values) : createCategory(values),
    onSuccess: () => {
      message.success(isEdit ? '已更新' : '已创建');
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      onClose();
    },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Drawer title={isEdit ? '编辑分类' : '新建分类'} placement="right" size="large" style={{ width: 480 }} open={open} onClose={onClose} destroyOnClose
      footer={<div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><Button onClick={onClose}>取消</Button><Button type="primary" loading={mutation.isPending} onClick={() => form.submit()}>保存</Button></div>}
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={editing || { sample_type: 'black', default_target_count: 100 }}>
        <Form.Item name="sample_type" label="样本类型" rules={[{ required: true }]}>
          <Select options={[{ value: 'black', label: '黑样本' }, { value: 'gray', label: '灰样本' }, { value: 'white', label: '白样本' }]} />
        </Form.Item>
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
        <Form.Item name="prompt_template_id" label="Prompt 模板" rules={[{ required: true }]}>
          <Select options={templates?.map((t) => ({ value: t.id, label: t.name }))} placeholder="选择模板" />
        </Form.Item>
        <Form.Item name="scenario_list_id" label="场景词库" rules={[{ required: true }]}>
          <Select options={wordlists?.filter((w) => w.kind === 'scenario').map((w) => ({ value: w.id, label: w.name }))} placeholder="选择场景词库" />
        </Form.Item>
        <Form.Item name="tone_list_id" label="语气词库" rules={[{ required: true }]}>
          <Select options={wordlists?.filter((w) => w.kind === 'tone').map((w) => ({ value: w.id, label: w.name }))} placeholder="选择语气词库" />
        </Form.Item>
        <Form.Item name="default_target_count" label="默认目标数量" rules={[{ required: true }]}><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
      </Form>
    </Drawer>
  );
}
