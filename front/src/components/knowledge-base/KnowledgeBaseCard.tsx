'use client';

import { Card, Button, Dropdown, Space, Modal, message } from 'antd';
import {
  EllipsisOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import type { KnowledgeBase } from '@/lib/types';
import { useRouter } from 'next/navigation';

interface KnowledgeBaseCardProps {
  knowledgeBase: KnowledgeBase;
  onDelete?: (id: number) => void;
  onEdit?: (kb: KnowledgeBase) => void;
}

export function KnowledgeBaseCard({ knowledgeBase, onDelete, onEdit }: KnowledgeBaseCardProps) {
  const router = useRouter();

  const handleDelete = () => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除知识库"${knowledgeBase.name}"吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => {
        onDelete?.(knowledgeBase.id);
        message.success('删除成功');
      },
    });
  };

  const menuItems: MenuProps['items'] = [
    {
      key: 'view',
      icon: <FolderOpenOutlined />,
      label: '查看详情',
      onClick: () => router.push(`/dashboard/knowledge-bases/${knowledgeBase.id}`),
    },
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑',
      onClick: () => onEdit?.(knowledgeBase),
    },
    {
      type: 'divider',
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除',
      danger: true,
      onClick: handleDelete,
    },
  ];

  return (
    <Card
      hoverable
      className="h-full border-0 shadow-lg hover:shadow-xl transition-all duration-300"
      style={{
        background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
      }}
      actions={[
        <Button
          type="text"
          icon={<FileTextOutlined />}
          onClick={() => router.push(`/dashboard/knowledge-bases/${knowledgeBase.id}/documents`)}
          className="text-slate-600 hover:text-teal-600"
        >
          文档管理
        </Button>,
        <Dropdown menu={{ items: menuItems }} trigger={['click']}>
          <Button
            type="text"
            icon={<EllipsisOutlined />}
            className="text-slate-600 hover:text-slate-800"
          />
        </Dropdown>,
      ]}
    >
      <div className="flex items-start gap-4 mb-4">
        <div
          className="w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg"
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          }}
        >
          <FolderOpenOutlined className="text-white text-xl" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg text-slate-800 truncate">
            {knowledgeBase.name}
          </h3>
          <p className="text-sm text-slate-500 line-clamp-2 mt-1">
            {knowledgeBase.description || '暂无描述'}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="px-3 py-1.5 rounded-lg text-white text-sm font-medium shadow-md"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            {knowledgeBase.document_count} 个文档
          </div>
        </div>
        <span className="text-xs text-slate-400">
          {new Date(knowledgeBase.updated_at).toLocaleDateString('zh-CN')}
        </span>
      </div>
    </Card>
  );
}
