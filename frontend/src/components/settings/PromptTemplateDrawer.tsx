import { Drawer, Form, Input, Button, message } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useMemo } from 'react';
import { createPromptTemplate, updatePromptTemplate } from '../../api/configs';
import type { PromptTemplateCreate, PromptTemplateOut } from '../../api/types';

interface Props { open: boolean; onClose: () => void; editing?: PromptTemplateOut; }

export function PromptTemplateDrawer({ open, onClose, editing }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!editing;
  const body = Form.useWatch('body', form);

  const variables = useMemo(() => {
    if (!body) return [];
    const matches = body.match(/\{([a-zA-Z_]\w*)\}/g);
    if (!matches) return [];
    return [...new Set(matches.map((m) => m.slice(1, -1)))];
  }, [body]);

  const mutation = useMutation({
    mutationFn: (values: PromptTemplateCreate) =>
      isEdit ? updatePromptTemplate(editing!.id, values) : createPromptTemplate(values),
    onSuccess: () => {
      message.success(isEdit ? '已更新' : '已创建');
      queryClient.invalidateQueries({ queryKey: ['prompt-templates'] });
      onClose();
    },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Drawer title={isEdit ? '编辑模板' : '新建模板'} placement="right" size="large" style={{ width: 560 }} open={open} onClose={onClose} destroyOnClose
      footer={<div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><Button onClick={onClose}>取消</Button><Button type="primary" loading={mutation.isPending} onClick={() => form.submit()}>保存</Button></div>}
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={editing || {}}>
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="body" label="模板内容" rules={[{ required: true }]} extra="使用 {variable} 语法定义变量">
          <Input.TextArea rows={8} placeholder="Generate a {tone} sample about {scenario}" />
        </Form.Item>
        <Form.Item label="检测到的变量">
          {variables.length > 0 ? (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {variables.map((v) => <code key={v} style={{ background: '#eff6ff', color: '#2563eb', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{v}</code>)}
            </div>
          ) : <span style={{ color: '#94a3b8', fontSize: 13 }}>未检测到变量</span>}
        </Form.Item>
      </Form>
    </Drawer>
  );
}
