'use client';

import { Modal, Form, Input, message } from 'antd';
import { useEffect, useState } from 'react';
import type { KnowledgeBase, CreateKnowledgeBaseRequest } from '@/lib/types';

interface CreateKnowledgeBaseModalProps {
  open: boolean;
  onCancel: () => void;
  onOk: (data: CreateKnowledgeBaseRequest) => Promise<{ success: boolean; error?: string }>;
  editingKB?: KnowledgeBase | null;
}

export function CreateKnowledgeBaseModal({
  open,
  onCancel,
  onOk,
  editingKB,
}: CreateKnowledgeBaseModalProps) {
  const [form] = Form.useForm();
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      if (editingKB) {
        form.setFieldsValue({
          name: editingKB.name,
          description: editingKB.description,
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, editingKB, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setIsSubmitting(true);

      const result = await onOk(values);

      if (result.success) {
        message.success(editingKB ? '更新成功' : '创建成功');
        form.resetFields();
        onCancel();
      } else {
        message.error(result.error || '操作失败');
      }
    } catch (error) {
      // Validation error
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      title={editingKB ? '编辑知识库' : '创建知识库'}
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={isSubmitting}
      okText={editingKB ? '更新' : '创建'}
      cancelText="取消"
    >
      <Form form={form} layout="vertical">
        <Form.Item
          label="知识库名称"
          name="name"
          rules={[
            { required: true, message: '请输入知识库名称' },
            { max: 100, message: '名称不能超过100个字符' },
          ]}
        >
          <Input placeholder="请输入知识库名称" />
        </Form.Item>

        <Form.Item
          label="描述"
          name="description"
          rules={[{ max: 500, message: '描述不能超过500个字符' }]}
        >
          <Input.TextArea
            rows={4}
            placeholder="请输入知识库描述（可选）"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
