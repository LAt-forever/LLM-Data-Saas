import { Drawer, Form, InputNumber, Select, Button, message, Tooltip, Divider } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { QuestionCircleOutlined } from '@ant-design/icons';
import { createTask } from '../../api/tasks';
import { listCategories, listApiConfigs } from '../../api/configs';
import type { TaskCreatePayload } from '../../api/types';

interface Props {
  open: boolean;
  onClose: () => void;
}

const HelpIcon = ({ title }: { title: string }) => (
  <Tooltip title={title}>
    <QuestionCircleOutlined style={{ color: '#94a3b8', marginLeft: 4, fontSize: 13 }} />
  </Tooltip>
);

const SectionTitle = ({ children }: { children: React.ReactNode }) => (
  <div
    style={{
      fontSize: 13,
      fontWeight: 600,
      color: '#475569',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      marginBottom: 12,
    }}
  >
    {children}
  </div>
);

export function TaskCreateDrawer({ open, onClose }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: categories, isLoading: loadingCategories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => listCategories(),
    enabled: open,
  });

  const { data: configs, isLoading: loadingConfigs } = useQuery({
    queryKey: ['api-configs'],
    queryFn: () => listApiConfigs(),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      message.success('任务已创建');
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
    <Drawer
      title="新建任务"
      placement="right"
      size="large"
      style={{ width: 520 }}
      open={open}
      onClose={onClose}
      destroyOnClose
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <Button onClick={onClose}>取消</Button>
          <Button
            type="primary"
            loading={mutation.isPending}
            onClick={() => form.submit()}
          >
            创建任务
          </Button>
        </div>
      }
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
        requiredMark={false}
      >
        <SectionTitle>基础配置</SectionTitle>

        <Form.Item
          name="category_id"
          label="分类"
          rules={[{ required: true, message: '请选择分类' }]}
        >
          <Select
            placeholder="选择分类"
            loading={loadingCategories}
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
            loading={loadingConfigs}
            options={configs?.map((c) => ({
              value: c.id,
              label: `${c.name} · ${c.model_name}`,
            }))}
          />
        </Form.Item>

        <Divider style={{ margin: '8px 0 20px' }} />

        <SectionTitle>运行参数</SectionTitle>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Form.Item
            name="target_count"
            label={
              <span>
                目标数量
                <HelpIcon title="任务需要生成的样本总数" />
              </span>
            }
            rules={[{ required: true }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="batch_size"
            label={
              <span>
                批次大小
                <HelpIcon title="每次 LLM 调用生成的样本数量（1-100）" />
              </span>
            }
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="max_workers"
            label={
              <span>
                并发数
                <HelpIcon title="同时进行的 LLM 请求数（1-50），越高越快但可能触发限流" />
              </span>
            }
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={50} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="max_per_file"
            label={
              <span>
                每文件最大条数
                <HelpIcon title="单个 CSV 输出文件包含的最大样本数，超过会自动分片" />
              </span>
            }
            rules={[{ required: true }]}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
        </div>
      </Form>
    </Drawer>
  );
}
