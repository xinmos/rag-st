import { apiClient } from './client';
import { mockKnowledgeBases } from './mock';
import type { BaseResponse, PaginatedResponse, KnowledgeBase, CreateKnowledgeBaseRequest } from '../types';

const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

export const knowledgeBaseApi = {
  /**
   * List knowledge bases
   */
  list: async (params: { page?: number; pageSize?: number } = {}) => {
    if (USE_MOCK_API) {
      const { page = 1, pageSize = 10 } = params;
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      const items = mockKnowledgeBases.slice(start, end);

      return Promise.resolve({
        code: 0,
        message: 'success',
        data: {
          total: mockKnowledgeBases.length,
          items,
        },
      } as BaseResponse<PaginatedResponse<KnowledgeBase>>);
    }

    return apiClient.post<BaseResponse<PaginatedResponse<KnowledgeBase>>>(
      '/api/v1/knowledge-base/list',
      params
    );
  },

  /**
   * Get knowledge base by ID (using query parameter)
   */
  getById: async (id: number) => {
    if (USE_MOCK_API) {
      const kb = mockKnowledgeBases.find((k) => k.id === id);
      if (!kb) {
        return Promise.reject({ response: { status: 404 } });
      }
      return Promise.resolve({
        code: 0,
        message: 'success',
        data: kb,
      } as BaseResponse<KnowledgeBase>);
    }

    return apiClient.post<BaseResponse<KnowledgeBase>>('/api/v1/knowledge-base/get', null, {
      params: { id },
    });
  },

  /**
   * Create knowledge base
   */
  create: async (data: CreateKnowledgeBaseRequest) => {
    if (USE_MOCK_API) {
      const newKB: KnowledgeBase = {
        id: Date.now(),
        ...data,
        document_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      mockKnowledgeBases.unshift(newKB);

      return Promise.resolve({
        code: 0,
        message: 'success',
        data: newKB,
      } as BaseResponse<KnowledgeBase>);
    }

    return apiClient.post<BaseResponse<KnowledgeBase>>('/api/v1/knowledge-base/create', data);
  },

  /**
   * Update knowledge base (using query parameter)
   */
  update: async (id: number, data: Partial<CreateKnowledgeBaseRequest>) => {
    if (USE_MOCK_API) {
      const kb = mockKnowledgeBases.find((k) => k.id === id);
      if (!kb) {
        return Promise.reject({ response: { status: 404 } });
      }
      Object.assign(kb, data, { updated_at: new Date().toISOString() });

      return Promise.resolve({
        code: 0,
        message: 'success',
        data: kb,
      } as BaseResponse<KnowledgeBase>);
    }

    return apiClient.post<BaseResponse<KnowledgeBase>>('/api/v1/knowledge-base/update', data, {
      params: { id },
    });
  },

  /**
   * Delete knowledge base (using query parameter)
   */
  delete: async (id: number) => {
    if (USE_MOCK_API) {
      const index = mockKnowledgeBases.findIndex((k) => k.id === id);
      if (index === -1) {
        return Promise.reject({ response: { status: 404 } });
      }
      mockKnowledgeBases.splice(index, 1);

      return Promise.resolve({
        code: 0,
        message: 'success',
        data: { deleted: true },
      } as BaseResponse<{ deleted: boolean }>);
    }

    return apiClient.post<BaseResponse<{ deleted: boolean }>>('/api/v1/knowledge-base/delete', null, {
      params: { id },
    });
  },
};
