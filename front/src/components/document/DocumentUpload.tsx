'use client';

import { useState } from 'react';
import { Upload, Button, Progress, List } from 'antd';
import { UploadOutlined, FileOutlined, DeleteOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { KnowledgeBase } from '@/lib/types';
import { useMessage } from '@/lib/hooks';
import { documentApi } from '@/lib/api/document';

interface DocumentUploadProps {
  knowledgeBaseId: number;
  onUploadComplete?: () => void;
}

interface UploadFile {
  uid: string;
  name: string;
  size: number;
  file: File;
  progress: number;
  status: 'uploading' | 'done' | 'error';
}

export function DocumentUpload({ knowledgeBaseId, onUploadComplete }: DocumentUploadProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const message = useMessage();

  const uploadProps: UploadProps = {
    accept: '.pdf,.doc,.docx,.txt,.md',
    multiple: true,
    showUploadList: false,
    beforeUpload: (file) => {
      const newFile: UploadFile = {
        uid: `${Date.now()}-${Math.random()}`,
        name: file.name,
        size: file.size,
        file,
        progress: 0,
        status: 'uploading',
      };
      setFiles((prev) => [...prev, newFile]);
      handleUpload(newFile);
      return false;
    },
  };

  const handleUpload = async (uploadFile: UploadFile) => {
    try {
      await documentApi.upload(knowledgeBaseId, uploadFile.file);

      setFiles((prev) =>
        prev.map((f) =>
          f.uid === uploadFile.uid ? { ...f, status: 'done', progress: 100 } : f
        )
      );

      message.success(`${uploadFile.name} 上传成功，正在处理中...`);
      onUploadComplete?.();
    } catch (error: any) {
      setFiles((prev) =>
        prev.map((f) =>
          f.uid === uploadFile.uid ? { ...f, status: 'error' } : f
        )
      );
      message.error(`${uploadFile.name} 上传失败: ${error.response?.data?.message || error.message || '未知错误'}`);
    }
  };

  const removeFile = (uid: string) => {
    setFiles((prev) => prev.filter((f) => f.uid !== uid));
  };

  return (
    <div>
      <Upload {...uploadProps}>
        <Button icon={<UploadOutlined />}>选择文件</Button>
      </Upload>

      {files.length > 0 && (
        <List
          className="mt-4"
          size="small"
          dataSource={files}
          renderItem={(file) => (
            <List.Item
              actions={[
                file.status === 'done' || file.status === 'error' ? (
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => removeFile(file.uid)}
                  />
                ) : null,
              ]}
            >
              <List.Item.Meta
                avatar={<FileOutlined className="text-gray-400" />}
                title={file.name}
                description={
                  file.status === 'uploading' ? (
                    <Progress percent={file.progress} size="small" />
                  ) : file.status === 'done' ? (
                    <span className="text-green-500">上传成功</span>
                  ) : (
                    <span className="text-red-500">上传失败</span>
                  )
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  );
}
