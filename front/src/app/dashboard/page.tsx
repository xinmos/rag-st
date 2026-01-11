'use client';

import { Card, Row, Col, Statistic } from 'antd';
import {
  DatabaseOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useKnowledgeBases } from '@/lib/hooks';

export default function DashboardPage() {
  const { knowledgeBases, isLoading } = useKnowledgeBases({ pageSize: 100 });

  const totalDocuments = knowledgeBases.reduce((sum, kb) => sum + kb.document_count, 0);

  return (
    <div className="p-6 min-h-full bg-gradient-to-br from-slate-50 to-sky-50/30">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">仪表盘</h1>
        <p className="text-slate-500 mt-1">欢迎使用 RAG-ST 智能问答系统</p>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-8">
        <Col xs={24} sm={12}>
          <Card
            className="border-0 shadow-lg hover:shadow-xl transition-shadow"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            <Statistic
              title={<span className="text-white/80">知识库数量</span>}
              value={knowledgeBases.length}
              prefix={<DatabaseOutlined className="text-white" />}
              valueStyle={{ color: '#fff' }}
              loading={isLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card
            className="border-0 shadow-lg hover:shadow-xl transition-shadow"
            style={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            }}
          >
            <Statistic
              title={<span className="text-white/80">文档总数</span>}
              value={totalDocuments}
              prefix={<FileTextOutlined className="text-white" />}
              valueStyle={{ color: '#fff' }}
              loading={isLoading}
            />
          </Card>
        </Col>
      </Row>

      {/* 最近的知识库 */}
      <Card
        title="最近的知识库"
        className="shadow-lg border-0"
        extra={
          knowledgeBases.length > 0 && (
            <span className="text-sm text-slate-500">共 {knowledgeBases.length} 个</span>
          )
        }
      >
        {knowledgeBases.slice(0, 5).map((kb) => (
          <div
            key={kb.id}
            className="flex items-center justify-between py-4 px-4 rounded-lg hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0"
          >
            <div className="flex-1">
              <div className="font-semibold text-slate-800">{kb.name}</div>
              <div className="text-sm text-slate-500 mt-1">{kb.description || '暂无描述'}</div>
            </div>
            <div className="flex items-center gap-3 ml-4">
              <div className="text-center px-4 py-2 rounded-lg bg-gradient-to-br from-teal-400 to-sky-500 text-white shadow-md">
                <div className="text-xs opacity-80">文档数</div>
                <div className="text-lg font-bold">{kb.document_count}</div>
              </div>
            </div>
          </div>
        ))}
        {knowledgeBases.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
              <DatabaseOutlined className="text-3xl text-slate-400" />
            </div>
            <p className="text-slate-500 mb-2">暂无知识库</p>
            <p className="text-sm text-slate-400">请先创建一个知识库开始使用</p>
          </div>
        )}
      </Card>
    </div>
  );
}
