import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { knowledgeBaseApi } from '@/lib/api';
import type { KnowledgeBase, CreateKnowledgeBaseRequest } from '@/lib/types';

interface KnowledgeBaseState {
  knowledgeBases: KnowledgeBase[];
  selectedKnowledgeBase: KnowledgeBase | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    total: number;
    page: number;
    pageSize: number;
  };
}

const initialState: KnowledgeBaseState = {
  knowledgeBases: [],
  selectedKnowledgeBase: null,
  isLoading: false,
  error: null,
  pagination: {
    total: 0,
    page: 1,
    pageSize: 10,
  },
};

// Async thunks
export const fetchKnowledgeBases = createAsyncThunk(
  'knowledgeBase/fetchAll',
  async (params: { page?: number; pageSize?: number } = {}, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseApi.list(params);
      const data = response.data as any;
      return data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || '获取知识库列表失败');
    }
  }
);

export const fetchKnowledgeBaseById = createAsyncThunk(
  'knowledgeBase/fetchById',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseApi.getById(id);
      return response.data as any;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || '获取知识库详情失败');
    }
  }
);

export const createKnowledgeBase = createAsyncThunk(
  'knowledgeBase/create',
  async (data: CreateKnowledgeBaseRequest, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseApi.create(data);
      return response.data as any;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || '创建知识库失败');
    }
  }
);

export const updateKnowledgeBase = createAsyncThunk(
  'knowledgeBase/update',
  async ({ id, data }: { id: number; data: Partial<CreateKnowledgeBaseRequest> }, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseApi.update(id, data);
      return response.data as any;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || '更新知识库失败');
    }
  }
);

export const deleteKnowledgeBase = createAsyncThunk(
  'knowledgeBase/delete',
  async (id: number, { rejectWithValue }) => {
    try {
      await knowledgeBaseApi.delete(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || '删除知识库失败');
    }
  }
);

// Slice
const knowledgeBaseSlice = createSlice({
  name: 'knowledgeBase',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearSelected: (state) => {
      state.selectedKnowledgeBase = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch all
      .addCase(fetchKnowledgeBases.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchKnowledgeBases.fulfilled, (state, action) => {
        state.isLoading = false;
        state.knowledgeBases = action.payload.items;
        state.pagination.total = action.payload.total;
      })
      .addCase(fetchKnowledgeBases.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch by ID
      .addCase(fetchKnowledgeBaseById.fulfilled, (state, action) => {
        state.selectedKnowledgeBase = action.payload;
      })
      // Create
      .addCase(createKnowledgeBase.fulfilled, (state, action) => {
        state.knowledgeBases.unshift(action.payload);
        state.pagination.total += 1;
      })
      // Update
      .addCase(updateKnowledgeBase.fulfilled, (state, action) => {
        const index = state.knowledgeBases.findIndex((kb) => kb.id === action.payload.id);
        if (index !== -1) {
          state.knowledgeBases[index] = action.payload;
        }
        if (state.selectedKnowledgeBase?.id === action.payload.id) {
          state.selectedKnowledgeBase = action.payload;
        }
      })
      // Delete
      .addCase(deleteKnowledgeBase.fulfilled, (state, action) => {
        state.knowledgeBases = state.knowledgeBases.filter((kb) => kb.id !== action.payload);
        state.pagination.total -= 1;
        if (state.selectedKnowledgeBase?.id === action.payload) {
          state.selectedKnowledgeBase = null;
        }
      });
  },
});

export const { clearError, clearSelected } = knowledgeBaseSlice.actions;
export default knowledgeBaseSlice.reducer;
