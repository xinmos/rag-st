import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { ChatMessage } from '@/lib/types';

interface ChatState {
  messages: ChatMessage[];
  currentChatId: string | null;
  knowledgeBaseId: number | null;
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [],
  currentChatId: null,
  knowledgeBaseId: null,
  isLoading: false,
  isStreaming: false,
  error: null,
};

// Slice
const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    updateMessage: (state, action) => {
      const index = state.messages.findIndex((m) => m.id === action.payload.id);
      if (index !== -1) {
        state.messages[index] = { ...state.messages[index], ...action.payload };
      }
    },
    setStreaming: (state, action) => {
      state.isStreaming = action.payload;
    },
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
    setKnowledgeBaseId: (state, action) => {
      state.knowledgeBaseId = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  addMessage,
  updateMessage,
  setStreaming,
  setLoading,
  clearMessages,
  setKnowledgeBaseId,
  setError,
  clearError,
} = chatSlice.actions;

export default chatSlice.reducer;
