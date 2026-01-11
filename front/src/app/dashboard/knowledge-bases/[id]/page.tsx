'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Button, Card, Descriptions, Spin, message } from 'antd';
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  MessageOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { knowledgeBaseApi } from '@/lib/api';
import type { KnowledgeBase } from '@/lib/types';

export default function KnowledgeBaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchKB = async () => {
      try {
        const response = await knowledgeBaseApi.getById(Number(params.id));
        setKnowledgeBase(response.data as KnowledgeBase);
      } catch (error) {
        message.error('获取知识库详情失败');
        router.push('/dashboard/knowledge-bases');
      } finally {
        setIsLoading(false);
      }
    };

    fetchKB();
  }, [params.id, router]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Spin size="large" />
      </div>
    );
  }

  if (!knowledgeBase) {
    return null;
  }

  return (
    <div className="p-6 min-h-full bg-gradient-to-br from-slate-50 to-sky-50/30">
      {/* 返回按钮 */}
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => router.push('/dashboard/knowledge-bases')}
        className="mb-6"
      >
        返回列表
      </Button>

      {/* 主卡片 */}
      <Card
        className="border-0 shadow-lg"
        title={
          <div className="flex items-center gap-3">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center shadow-lg"
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              }}
            >
              <DatabaseOutlined className="text-white text-xl" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800">{knowledgeBase.name}</h2>
              <p className="text-sm text-slate-500">知识库详情</p>
            </div>
          </div>
        }
      >
        {/* 统计信息 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div
            className="p-4 rounded-xl text-white shadow-lg"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-80 mb-1">文档数量</div>
                <div className="text-3xl font-bold">{knowledgeBase.document_count}</div>
              </div>
              <FileTextOutlined className="text-4xl opacity-50" />
            </div>
          </div>

          <div
            className="p-4 rounded-xl text-white shadow-lg"
            style={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            }}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-80 mb-1">创建时间</div>
                <div className="text-sm font-medium">
                  {new Date(knowledgeBase.created_at).toLocaleDateString('zh-CN')}
                </div>
              </div>
              <ClockCircleOutlined className="text-3xl opacity-50" />
            </div>
          </div>

          <div
            className="p-4 rounded-xl text-white shadow-lg"
            style={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            }}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-80 mb-1">更新时间</div>
                <div className="text-sm font-medium">
                  {new Date(knowledgeBase.updated_at).toLocaleDateString('zh-CN')}
                </div>
              </div>
              <ClockCircleOutlined className="text-3xl opacity-50" />
            </div>
          </div>
        </div>

        {/* 详细信息 */}
        <div className="bg-white rounded-xl p-6 border border-slate-200">
          <h3 className="text-lg font-semibold mb-4 text-slate-800">详细信息</h3>
          <Descriptions column={1} bordered>
            <Descriptions.Item label="知识库名称">
              {knowledgeBase.name}
            </Descriptions.Item>
            <Descriptions.Item label="描述">
              {knowledgeBase.description || '暂无描述'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(knowledgeBase.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {new Date(knowledgeBase.updated_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3 mt-6">
          <Button
            type="primary"
            size="large"
            icon={<FileTextOutlined />}
            onClick={() => router.push(`/dashboard/knowledge-bases/${knowledgeBase.id}/documents`)}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
            }}
          >
            管理文档
          </Button>
          <Button
            size="large"
            icon={<MessageOutlined />}
            onClick={() => router.push(`/dashboard/chat/${knowledgeBase.id}`)}
          >
            开始对话
          </Button>
        </div>
      </Card>
    </div>
  );
}
