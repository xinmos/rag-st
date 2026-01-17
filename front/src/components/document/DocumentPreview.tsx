'use client';

import { Modal } from 'antd';
import { useEffect, useState } from 'react';

interface DocumentPreviewProps {
  visible: boolean;
  documentId: number | null;
  fileName: string;
  fileType: string;
  onClose: () => void;
}

// 支持浏览器内预览的文件类型
const PREVIEWABLE_TYPES = [
  'application/pdf',
  'text/plain',
  'text/markdown',
  'text/html',
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
];

export function DocumentPreview({
  visible,
  documentId,
  fileName,
  fileType,
  onClose,
}: DocumentPreviewProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (visible && documentId) {
      loadPreview();
    }
    // Cleanup blob URL when modal closes or component unmounts
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
      }
    };
  }, [visible, documentId]);

  const loadPreview = async () => {
    if (!documentId) return;

    setLoading(true);
    try {
      const { documentApi } = await import('@/lib/api');
      const url = await documentApi.preview(documentId);
      setPreviewUrl(url);
    } catch (error) {
      console.error('Failed to load preview:', error);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const canPreview = PREVIEWABLE_TYPES.includes(fileType);

  if (!visible) return null;

  return (
    <Modal
      title={fileName}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={canPreview ? '80%' : 500}
      style={{ top: 20 }}
    >
      {loading && <div className="text-center py-8">加载中...</div>}

      {!loading && !canPreview && (
        <div className="text-center py-8">
          <p className="mb-4">此文件类型不支持浏览器内预览</p>
          <p className="text-gray-500">请使用下载按钮保存文件后使用相应程序打开</p>
        </div>
      )}

      {!loading && canPreview && previewUrl && (
        <div className="w-full" style={{ height: '70vh' }}>
          {fileType === 'application/pdf' ? (
            <iframe
              src={previewUrl}
              className="w-full h-full border-0"
              title={fileName}
            />
          ) : fileType.startsWith('image/') ? (
            <div className="flex items-center justify-center h-full">
              <img
                src={previewUrl}
                alt={fileName}
                className="max-w-full max-h-full object-contain"
              />
            </div>
          ) : (
            <iframe
              src={previewUrl}
              className="w-full h-full border-0"
              title={fileName}
            />
          )}
        </div>
      )}
    </Modal>
  );
}
