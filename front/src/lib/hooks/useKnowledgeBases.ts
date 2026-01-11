import { useCallback, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from './redux';
import {
  fetchKnowledgeBases,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  clearError as clearKbError,
} from '@/lib/store/slices/knowledgeBaseSlice';
import type { CreateKnowledgeBaseRequest } from '@/lib/types';

export function useKnowledgeBases(params: { page?: number; pageSize?: number } = {}) {
  const dispatch = useAppDispatch();
  const { knowledgeBases, selectedKnowledgeBase, isLoading, error, pagination } = useAppSelector(
    (state) => state.knowledgeBases
  );

  // Fetch knowledge bases on mount or when params change
  useEffect(() => {
    dispatch(fetchKnowledgeBases(params));
  }, [dispatch, params.page, params.pageSize]);

  const handleCreate = useCallback(
    async (data: CreateKnowledgeBaseRequest) => {
      const result = await dispatch(createKnowledgeBase(data));
      return {
        success: createKnowledgeBase.fulfilled.match(result),
        error: result.payload as string | undefined,
      };
    },
    [dispatch]
  );

  const handleUpdate = useCallback(
    async (id: number, data: Partial<CreateKnowledgeBaseRequest>) => {
      const result = await dispatch(updateKnowledgeBase({ id, data }));
      return {
        success: updateKnowledgeBase.fulfilled.match(result),
        error: result.payload as string | undefined,
      };
    },
    [dispatch]
  );

  const handleDelete = useCallback(
    async (id: number) => {
      const result = await dispatch(deleteKnowledgeBase(id));
      return {
        success: deleteKnowledgeBase.fulfilled.match(result),
        error: result.payload as string | undefined,
      };
    },
    [dispatch]
  );

  const refetch = useCallback(() => {
    dispatch(fetchKnowledgeBases(params));
  }, [dispatch, params]);

  return {
    knowledgeBases,
    selectedKnowledgeBase,
    isLoading,
    error,
    pagination,
    create: handleCreate,
    update: handleUpdate,
    delete: handleDelete,
    refetch,
    clearError: () => dispatch(clearKbError()),
  };
}
