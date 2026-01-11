'use client';

import { useState } from 'react';
import { Button, Row, Col, Empty, Spin } from 'antd';
import { PlusOutlined, DatabaseOutlined } from '@ant-design/icons';
import { useKnowledgeBases } from '@/lib/hooks';
import { KnowledgeBaseCard } from '@/components/knowledge-base/KnowledgeBaseCard';
import { CreateKnowledgeBaseModal } from '@/components/knowledge-base/CreateKnowledgeBaseModal';
import type { KnowledgeBase } from '@/lib/types';

export default function KnowledgeBasesPage() {
  const { knowledgeBases, isLoading, create, delete: deleteKB, update } = useKnowledgeBases();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingKB, setEditingKB] = useState<KnowledgeBase | null>(null);

  const handleCreate = () => {
    setEditingKB(null);
    setModalOpen(true);
  };

  const handleEdit = (kb: KnowledgeBase) => {
    setEditingKB(kb);
    setModalOpen(true);
  };

  const handleModalOk = async (data: { name: string; description: string }) => {
    if (editingKB) {
      return await update(editingKB.id, data);
    }
    return await create(data);
  };

  return (
    <div className="p-6 min-h-full bg-gradient-to-br from-slate-50 to-sky-50/30">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">知识库管理</h1>
          <p className="text-slate-500 mt-1">创建和管理您的知识库</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          className="shadow-lg hover:shadow-xl transition-shadow"
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            border: 'none',
          }}
        >
          创建知识库
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Spin size="large" />
        </div>
      ) : knowledgeBases.length === 0 ? (
        <Empty
          description={
            <div className="py-8">
              <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
                <DatabaseOutlined className="text-4xl text-slate-400" />
              </div>
              <p className="text-lg font-medium text-slate-700 mb-2">暂无知识库</p>
              <p className="text-sm text-slate-500 mb-6">创建第一个知识库开始使用</p>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleCreate}
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                }}
              >
                创建第一个知识库
              </Button>
            </div>
          }
          image={null}
        />
      ) : (
        <Row gutter={[16, 16]}>
          {knowledgeBases.map((kb) => (
            <Col xs={24} sm={12} lg={8} xl={6} key={kb.id}>
              <KnowledgeBaseCard
                knowledgeBase={kb}
                onEdit={handleEdit}
                onDelete={deleteKB}
              />
            </Col>
          ))}
        </Row>
      )}

      <CreateKnowledgeBaseModal
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleModalOk}
        editingKB={editingKB}
      />
    </div>
  );
}
