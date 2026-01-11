'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button, Card, Input, Row, Col, Spin, Empty, message } from 'antd';
import { ArrowLeftOutlined, SearchOutlined } from '@ant-design/icons';
import { useDocuments } from '@/lib/hooks';
import { knowledgeBaseApi } from '@/lib/api';
import { DocumentCard } from '@/components/document/DocumentCard';
import { DocumentUpload } from '@/components/document/DocumentUpload';
import type { KnowledgeBase } from '@/lib/types';

export default function DocumentsPage() {
  const params = useParams();
  const router = useRouter();
  const { documents, isLoading, fetchDocuments, deleteDocument } = useDocuments(
    Number(params.id)
  );
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [searchText, setSearchText] = useState('');
  const [hasProcessing, setHasProcessing] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch knowledge base info
  const fetchKnowledgeBase = useCallback(async () => {
    try {
      const response = await knowledgeBaseApi.getById(Number(params.id));
      setKnowledgeBase(response.data as KnowledgeBase);
    } catch (error) {
      router.push('/dashboard/knowledge-bases');
    }
  }, [params.id, router]);

  // Refresh both documents and KB info
  const refreshAll = useCallback(() => {
    fetchDocuments();
    fetchKnowledgeBase();
  }, [fetchDocuments, fetchKnowledgeBase]);

  // Initial fetch
  useEffect(() => {
    refreshAll();
  }, []); // Only run once on mount

  // Check for processing documents and start/stop polling
  useEffect(() => {
    const processingCount = documents.filter(doc => doc.status === 'processing').length;
    const shouldPoll = processingCount > 0;

    setHasProcessing(shouldPoll);

    // Clear existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Start polling only if there are processing documents
    if (shouldPoll) {
      intervalRef.current = setInterval(() => {
        refreshAll();
      }, 3000);
    }

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [documents]); // Only depend on documents to check status

  const handleUploadComplete = useCallback(() => {
    // Refresh both document list and knowledge base info (including document count)
    refreshAll();
  }, [refreshAll]);

  const handleDelete = async (documentId: number) => {
    const result = await deleteDocument(documentId);
    if (result.success) {
      message.success('删除成功');
      // Refresh knowledge base info to update document count
      refreshAll();
    }
  };

  const filteredDocuments = documents.filter((doc) =>
    doc.file_name.toLowerCase().includes(searchText.toLowerCase())
  );

  if (!knowledgeBase) {
    return (
      <div className="flex justify-center py-12">
        <Spin size="large" />
      </div>
    );
  }

  const processingCount = documents.filter(doc => doc.status === 'processing').length;

  // Memoize hasProcessing to avoid unnecessary re-renders
  const hasProcessingDocs = processingCount > 0;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => router.push('/dashboard/knowledge-bases')}
          >
            返回
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{knowledgeBase.name}</h1>
            <p className="text-gray-500 text-sm">
              {knowledgeBase.description} · {knowledgeBase.document_count} 个文档
              {processingCount > 0 && (
                <span className="ml-2 text-blue-500">
                  · {processingCount} 个文档处理中...
                </span>
              )}
            </p>
          </div>
        </div>
        <Button onClick={refreshAll} loading={isLoading}>
          刷新
        </Button>
      </div>

      <Card title="上传文档" className="mb-6">
        <DocumentUpload
          knowledgeBaseId={knowledgeBase.id}
          onUploadComplete={handleUploadComplete}
        />
      </Card>

      <Card
        title="文档列表"
        extra={
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索文档"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
        }
      >
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Spin size="large" />
          </div>
        ) : filteredDocuments.length === 0 ? (
          <Empty
            description={searchText ? '没有找到匹配的文档' : '暂无文档'}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            className="py-12"
          />
        ) : (
          <Row gutter={[16, 16]}>
            {filteredDocuments.map((doc) => (
              <Col xs={24} sm={12} lg={8} key={doc.id}>
                <DocumentCard document={doc} onDelete={handleDelete} />
              </Col>
            ))}
          </Row>
        )}
      </Card>
    </div>
  );
}
