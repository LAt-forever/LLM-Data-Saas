import { Drawer, Form, Input, Select, Button, message } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createApiConfig, updateApiConfig } from '../../api/configs';
import type { ApiConfigCreate, ApiConfigOut } from '../../api/types';

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: ApiConfigOut;
}

export function ApiConfigDrawer({ open, onClose, editing }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!editing;

  const mutation = useMutation({
    mutationFn: (values: ApiConfigCreate) =>
      isEdit ? updateApiConfig(editing!.id, values) : createApiConfig(values),
    onSuccess: () => {
      message.success(isEdit ? '配置已更新' : '配置已创建');
      queryClient.invalidateQueries({ queryKey: ['api-configs'] });
      onClose();
    },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Drawer
      title={isEdit ? '编辑 API 配置' : '新建 API 配置'}
      placement="right"
      size="large"
      style={{ width: 480 }}
      open={open}
      onClose={onClose}
      destroyOnClose
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" loading={mutation.isPending} onClick={() => form.submit()}>保存</Button>
        </div>
      }
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={editing || { type: 'openai' }}>
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="base_url" label="Base URL" rules={[{ required: true }]}><Input placeholder="https://api.example.com/v1" /></Form.Item>
        <Form.Item name="api_key" label="API Key" rules={[{ required: !isEdit }]}><Input.Password placeholder={isEdit ? '留空表示不修改' : ''} /></Form.Item>
        <Form.Item name="model_name" label="模型名称" rules={[{ required: true }]}><Input placeholder="gpt-4, deepseek-chat..." /></Form.Item>
        <Form.Item name="type" label="类型" rules={[{ required: true }]}>
          <Select options={[{ value: 'openai', label: 'OpenAI 兼容' }, { value: 'raw', label: 'Raw HTTP' }]} />
        </Form.Item>
      </Form>
    </Drawer>
  );
}
