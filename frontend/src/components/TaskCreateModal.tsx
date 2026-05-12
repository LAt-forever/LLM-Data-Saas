import { Modal, Form, InputNumber, Select, Button, Space, message } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createTask } from '../api/tasks';
import { listCategories, listApiConfigs } from '../api/configs';
import type { TaskCreatePayload } from '../api/types';

interface Props {
  open: boolean;
  onClose: () => void;
}

export function TaskCreateModal({ open, onClose }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => listCategories(),
    enabled: open,
  });

  const { data: configs } = useQuery({
    queryKey: ['api-configs'],
    queryFn: () => listApiConfigs(),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      message.success('任务创建成功');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      form.resetFields();
      onClose();
    },
    onError: (err: Error) => {
      message.error(`创建失败: ${err.message}`);
    },
  });

  const handleSubmit = (values: TaskCreatePayload) => {
    mutation.mutate(values);
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="新建任务"
      footer={null}
      destroyOnClose
      width={560}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          target_count: 1000,
          batch_size: 10,
          max_workers: 5,
          max_per_file: 10000,
        }}
      >
        <Form.Item
          name="category_id"
          label="分类"
          rules={[{ required: true, message: '请选择分类' }]}
        >
          <Select
            placeholder="选择分类"
            options={categories?.map((c) => ({
              value: c.id,
              label: `[${c.sample_type}] ${c.name}`,
            }))}
            showSearch
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
          />
        </Form.Item>

        <Form.Item
          name="api_config_id"
          label="API 配置"
          rules={[{ required: true, message: '请选择 API 配置' }]}
        >
          <Select
            placeholder="选择 API 配置"
            options={configs?.map((c) => ({
              value: c.id,
              label: `${c.name} (${c.model_name})`,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="target_count"
          label="目标数量"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="batch_size"
          label="批次大小"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} max={100} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="max_workers"
          label="并发数"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} max={50} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="max_per_file"
          label="每文件最大条数"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={mutation.isPending}>
              创建
            </Button>
            <Button onClick={onClose}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
