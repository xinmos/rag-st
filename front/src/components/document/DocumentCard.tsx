'use client';

import { Card, Button, Space, Popconfirm, message, Progress } from 'antd';
import {
  FileOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { Document } from '@/lib/types';
import { DocumentStatusBadge } from './DocumentStatusBadge';
import { DocumentPreview } from './DocumentPreview';
import { useState } from 'react';

interface DocumentCardProps {
  document: Document;
  onDelete?: (id: number) => void;
}

export function DocumentCard({ document, onDelete }: DocumentCardProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);

  const handlePreview = () => {
    if (document.status !== 'completed') {
      message.warning('文档处理中，预览功能暂不可用');
      return;
    }
    setPreviewVisible(true);
  };

  const handleDownload = async () => {
    if (document.status !== 'completed') {
      message.warning('文档处理中，下载功能暂不可用');
      return;
    }

    setIsDownloading(true);
    try {
      const { documentApi } = await import('@/lib/api');
      await documentApi.download(document.id, document.file_name);
      message.success('下载成功');
    } catch (error) {
      console.error('Download failed:', error);
      message.error('下载失败');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDelete = () => {
    onDelete?.(document.id);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const showProgress = document.status === 'processing' && document.progress > 0;
  const canPreview = document.status === 'completed';

  return (
    <>
      <Card
        size="small"
        className="hover:shadow-md transition-shadow"
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded bg-gray-100 flex items-center justify-center flex-shrink-0">
            <FileOutlined className="text-gray-500" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-medium truncate">{document.file_name}</div>
            <div className="text-sm text-gray-500 mt-1">
              {formatFileSize(document.file_size)} · <DocumentStatusBadge status={document.status} />
              {document.chunk_count && document.status === 'completed' && (
                <span className="ml-2">· {document.chunk_count} 个分块</span>
              )}
            </div>
            {showProgress && (
              <div className="mt-2">
                <Progress
                  percent={document.progress}
                  size="small"
                  status="active"
                  strokeColor="#1890ff"
                />
              </div>
            )}
            {document.status === 'failed' && document.error_message && (
              <div className="text-xs text-red-500 mt-1 truncate" title={document.error_message}>
                错误: {document.error_message}
              </div>
            )}
            <div className="text-xs text-gray-400 mt-1">
              {new Date(document.created_at).toLocaleString('zh-CN')}
            </div>
          </div>
          <Space size="small">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={handlePreview}
              disabled={!canPreview}
              title="预览"
            />
            <Button
              type="text"
              icon={<DownloadOutlined />}
              size="small"
              onClick={handleDownload}
              disabled={!canPreview}
              loading={isDownloading}
              title="下载"
            />
            <Popconfirm
              title="确认删除"
              description="确定要删除这个文档吗？"
              onConfirm={handleDelete}
              okText="删除"
              cancelText="取消"
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                size="small"
                title="删除"
              />
            </Popconfirm>
          </Space>
        </div>
      </Card>

      <DocumentPreview
        visible={previewVisible}
        documentId={canPreview ? document.id : null}
        fileName={document.file_name}
        fileType={document.file_type}
        onClose={() => setPreviewVisible(false)}
      />
    </>
  );
}
