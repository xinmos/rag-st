import { useCallback, useState } from 'react';
import { documentApi } from '@/lib/api';
import type { Document } from '@/lib/types';

export function useDocuments(knowledgeBaseId: number) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ total: 0, page: 1, pageSize: 10 });

  const fetchDocuments = useCallback(
    async (params: { page?: number; pageSize?: number } = {}) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await documentApi.list(knowledgeBaseId, params);
        const data = response.data as any;
        setDocuments(data.items || []);
        setPagination({
          total: data.total || 0,
          page: params.page || 1,
          pageSize: params.pageSize || 10,
        });
      } catch (err: any) {
        setError(err.response?.data?.detail || '获取文档列表失败');
      } finally {
        setIsLoading(false);
      }
    },
    [knowledgeBaseId]
  );

  const uploadDocument = useCallback(
    async (file: File, onProgress?: (progress: number) => void) => {
      setError(null);
      try {
        const response = await documentApi.upload(knowledgeBaseId, file, onProgress);
        const doc = response.data as any;
        setDocuments((prev) => [doc, ...prev]);
        setPagination((prev) => ({ ...prev, total: prev.total + 1 }));
        return { success: true, data: doc };
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || '上传文档失败';
        setError(errorMsg);
        return { success: false, error: errorMsg };
      }
    },
    [knowledgeBaseId]
  );

  const deleteDocument = useCallback(
    async (documentId: number) => {
      setError(null);
      try {
        await documentApi.delete(knowledgeBaseId, documentId);
        setDocuments((prev) => prev.filter((d) => d.id !== documentId));
        setPagination((prev) => ({ ...prev, total: prev.total - 1 }));
        return { success: true };
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || '删除文档失败';
        setError(errorMsg);
        return { success: false, error: errorMsg };
      }
    },
    [knowledgeBaseId]
  );

  return {
    documents,
    isLoading,
    error,
    pagination,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
    clearError: () => setError(null),
  };
}
