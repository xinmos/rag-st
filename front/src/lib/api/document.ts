import { apiClient } from './client';
import { mockDocuments } from './mock';
import type { BaseResponse, PaginatedResponse, Document } from '../types';

const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

export const documentApi = {
  /**
   * List documents by knowledge base ID
   */
  list: async (knowledgeBaseId: number, params: { page?: number; pageSize?: number } = {}) => {
    if (USE_MOCK_API) {
      const { page = 1, pageSize = 10 } = params;
      const kbDocuments = mockDocuments.filter((d) => d.knowledge_base_id === knowledgeBaseId);
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      const items = kbDocuments.slice(start, end);

      return Promise.resolve({
        code: 0,
        message: 'success',
        data: {
          total: kbDocuments.length,
          items,
        },
      } as BaseResponse<PaginatedResponse<Document>>);
    }

    return apiClient.post<BaseResponse<PaginatedResponse<Document>>>(
      '/api/v1/document/list',
      { ...params, knowledge_base_id: knowledgeBaseId }
    );
  },

  /**
   * Upload document
   */
  upload: async (knowledgeBaseId: number, file: File, onProgress?: (progress: number) => void) => {
    if (USE_MOCK_API) {
      // Simulate upload progress
      if (onProgress) {
        for (let i = 0; i <= 100; i += 10) {
          await new Promise((resolve) => setTimeout(resolve, 100));
          onProgress(i);
        }
      }

      const newDoc: Document = {
        id: Date.now(),
        knowledge_base_id: knowledgeBaseId,
        file_name: file.name,
        file_size: file.size,
        file_type: file.type,
        status: 'processing',
        progress: 0,  // 初始进度
        created_at: new Date().toISOString(),
      };
      mockDocuments.unshift(newDoc);

      return Promise.resolve({
        code: 0,
        message: 'success',
        data: newDoc,
      } as BaseResponse<Document>);
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('knowledge_base_id', String(knowledgeBaseId));  // 作为 form-data

    return apiClient.post<BaseResponse<Document>>(
      '/api/v1/document/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      }
    );
  },

  /**
   * Delete document (using query parameter)
   */
  delete: async (knowledgeBaseId: number, documentId: number) => {
    if (USE_MOCK_API) {
      const index = mockDocuments.findIndex((d) => d.id === documentId);
      if (index === -1) {
        return Promise.reject({ response: { status: 404 } });
      }
      mockDocuments.splice(index, 1);

      return Promise.resolve({
        code: 0,
        message: 'success',
        data: { deleted: true },
      } as BaseResponse<{ deleted: boolean }>);
    }

    return apiClient.post<BaseResponse<{ deleted: boolean }>>(
      '/api/v1/document/delete',
      null,
      { params: { knowledge_base_id: knowledgeBaseId, document_id: documentId } }
    );
  },

  /**
   * Preview document - returns blob URL
   */
  preview: async (documentId: number): Promise<string> => {
    if (USE_MOCK_API) {
      // Mock: return a dummy blob URL
      const mockContent = 'Mock document content';
      const blob = new Blob([mockContent], { type: 'application/pdf' });
      return Promise.resolve(URL.createObjectURL(blob));
    }

    try {
      const response = await apiClient.get(`/api/v1/document/preview/${documentId}`, {
        responseType: 'blob',
      });

      console.log('[preview] Response:', {
        status: response.status,
        headers: response.headers,
        dataType: typeof response.data,
        dataIsBlob: response.data instanceof Blob,
        dataSize: response.data?.size,
      });

      // Handle different response structures
      let blobData: Blob;
      if (response.data instanceof Blob) {
        blobData = response.data;
      } else {
        console.warn('[preview] Response data is not a Blob, converting...');
        blobData = new Blob([response.data]);
      }

      const contentType = response.headers['content-type'] || 'application/octet-stream';
      return URL.createObjectURL(blobData);
    } catch (error) {
      console.error('[preview] Error:', error);
      throw error;
    }
  },

  /**
   * Download document - triggers browser download
   */
  download: async (documentId: number, fileName: string): Promise<void> => {
    if (USE_MOCK_API) {
      // Mock: create a dummy file and trigger download
      const mockContent = 'Mock document content';
      const blob = new Blob([mockContent], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      return Promise.resolve();
    }

    console.log('[download] Starting download for document:', documentId, fileName);

    try {
      const response = await apiClient.get(`/api/v1/document/preview/${documentId}`, {
        responseType: 'blob',
      });

      console.log('[download] Response:', {
        status: response.status,
        headers: response.headers,
        dataType: typeof response.data,
        dataIsBlob: response.data instanceof Blob,
        dataSize: response.data?.size,
      });

      // Handle different response structures
      let blobData: Blob;
      if (response.data instanceof Blob) {
        blobData = response.data;
      } else {
        console.warn('[download] Response data is not a Blob, converting...');
        blobData = new Blob([response.data]);
      }

      const contentType = response.headers['content-type'] || 'application/octet-stream';
      const url = URL.createObjectURL(blobData);

      console.log('[download] Created blob URL:', url, 'size:', blobData.size, 'type:', contentType);

      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      console.log('[download] Download triggered successfully');
    } catch (error) {
      console.error('[download] Error:', error);
      throw error;
    }
  },
};
