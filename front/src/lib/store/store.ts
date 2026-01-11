import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import knowledgeBaseReducer from './slices/knowledgeBaseSlice';
import chatReducer from './slices/chatSlice';

// Create store
export const store = configureStore({
  reducer: {
    auth: authReducer,
    knowledgeBases: knowledgeBaseReducer,
    chat: chatReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['chat/addMessage', 'chat/updateMessage'],
      },
    }),
});

// Infer types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
