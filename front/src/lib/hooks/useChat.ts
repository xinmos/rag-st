import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from './redux';
import {
  addMessage,
  updateMessage,
  setStreaming,
  setLoading,
  clearMessages,
  setKnowledgeBaseId,
  setError,
} from '@/lib/store/slices/chatSlice';
import { chatApi } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';

export function useChat() {
  const dispatch = useAppDispatch();
  const { messages, currentChatId, knowledgeBaseId, isLoading, isStreaming, error } = useAppSelector(
    (state) => state.chat
  );

  const sendMessage = useCallback(
    async (question: string, kbId?: number) => {
      // Add user message
      const userMessage: ChatMessage = {
        id: Date.now(),
        role: 'user',
        content: question,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(userMessage));

      // Set knowledge base if provided
      if (kbId !== undefined) {
        dispatch(setKnowledgeBaseId(kbId));
      }

      // Create placeholder for assistant message
      const assistantMessageId = Date.now() + 1;
      dispatch(
        addMessage({
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          references: [],
        })
      );

      dispatch(setStreaming(true));
      let fullResponse = '';

      try {
        // Stream response
        let chunkCount = 0;
        for await (const chunk of chatApi.chat(question, kbId)) {
          chunkCount++;
          fullResponse += chunk;
          console.log(`🔄 更新消息 #${chunkCount}: 当前长度 ${fullResponse.length}`);
          dispatch(
            updateMessage({
              id: assistantMessageId,
              content: fullResponse,
            })
          );
        }
        console.log(`✅ 流式完成，总共 ${chunkCount} 个块，最终长度: ${fullResponse.length}`);
      } catch (err: any) {
        dispatch(
          updateMessage({
            id: assistantMessageId,
            content: '抱歉，发生了错误，请稍后重试。',
          })
        );
        setError(err.message || '聊天失败');
      } finally {
        dispatch(setStreaming(false));
      }
    },
    [dispatch]
  );

  const clearChat = useCallback(() => {
    dispatch(clearMessages());
  }, [dispatch]);

  return {
    messages,
    currentChatId,
    knowledgeBaseId,
    isLoading,
    isStreaming,
    error,
    sendMessage,
    clearChat,
    clearError: () => dispatch(setError(null)),
  };
}
