import { apiClient } from './client';
import { mockStreamChatResponse } from './mock';
import type { ChatRequest, ChatResponse, BaseResponse } from '../types';

const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

// Socket.IO client (lazy load)
let socketIOClient: any = null;
let connectionPromise: Promise<any> | null = null;

/**
 * Initialize Socket.IO client
 */
async function initSocketIO(): Promise<any> {
  if (typeof window === 'undefined') {
    throw new Error('Socket.IO only works in browser');
  }

  if (socketIOClient && socketIOClient.connected) {
    return socketIOClient;
  }

  // Use existing connection promise
  if (connectionPromise) {
    return connectionPromise;
  }

  connectionPromise = new Promise((resolve, reject) => {
    // Dynamic import for socket.io-client
    import('socket.io-client').then(({ io }) => {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('auth_token');

      socketIOClient = io(API_BASE_URL, {
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        auth: { token },
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      socketIOClient.on('connect', () => {
        console.log('Socket.IO connected');
        resolve(socketIOClient);
      });

      socketIOClient.on('disconnect', () => {
        console.log('Socket.IO disconnected');
      });

      socketIOClient.on('connect_error', (error: any) => {
        console.error('Socket.IO connect error:', error);
        connectionPromise = null;
        reject(error);
      });

      socketIOClient.on('error', (error: any) => {
        console.error('Socket.IO error:', error);
      });

      // Timeout after 5 seconds
      setTimeout(() => {
        if (!socketIOClient.connected) {
          connectionPromise = null;
          reject(new Error('Socket.IO connection timeout'));
        }
      }, 5000);
    });
  });

  return connectionPromise;
}

export const chatApi = {
  /**
   * Send chat message and stream response using Socket.IO
   */
  chat: async function* (question: string, knowledgeBaseId?: number): AsyncGenerator<string, void, unknown> {
    if (USE_MOCK_API) {
      yield* mockStreamChatResponse(question, knowledgeBaseId?.toString());
      return;
    }

    // Get Socket.IO client
    const socket = await initSocketIO();

    // Create a queue for streaming
    const queue: string[] = [];
    let done = false;
    let error: Error | null = null;
    let resolver: ((value: void) => void) | null = null;

    const waitForChunk = () => new Promise<void>((resolve, reject) => {
      if (error) return reject(error);
      if (done && queue.length === 0) return resolve();
      resolver = resolve;
    });

    const onChatChunk = (data: { content: string; is_complete: boolean }) => {
      console.log('📨 收到 chat_chunk:', data);
      queue.push(data.content);
      if (resolver) {
        resolver();
        resolver = null;
      }
    };

    const onChatComplete = (data: { answer: string; sources: any[] }) => {
      console.log('✅ 收到 chat_complete:', data);
      done = true;
      if (resolver) {
        resolver();
        resolver = null;
      }
    };

    const onError = (data: { message: string }) => {
      console.error('❌ 收到 error:', data);
      error = new Error(data.message);
      if (resolver) {
        resolver();
        resolver = null;
      }
    };

    // Register listeners
    socket.on('chat_chunk', onChatChunk);
    socket.on('chat_complete', onChatComplete);
    socket.on('error', onError);

    try {
      // Send chat message
      const messageData = {
        knowledge_base_id: knowledgeBaseId,
        message: question,
      };
      console.log('📤 发送消息:', messageData);
      socket.emit('chat_message', messageData);

      // Stream chunks as they arrive
      console.log('⏳ 等待响应...');
      let chunkCount = 0;
      while (!done || queue.length > 0) {
        if (error) throw error;
        if (queue.length === 0) {
          await waitForChunk();
          continue;
        }
        const chunk = queue.shift();
        if (chunk) {
          chunkCount++;
          console.log(`📦 收到第 ${chunkCount} 个块, 长度: ${chunk.length}, 内容: ${chunk.substring(0, 20)}...`);
          yield chunk;
        }
      }
      console.log(`✅ 总共收到 ${chunkCount} 个块`);
    } finally {
      // Clean up listeners
      socket.off('chat_chunk', onChatChunk);
      socket.off('chat_complete', onChatComplete);
      socket.off('error', onError);
    }
  },

  /**
   * Non-streaming chat (for fallback)
   */
  chatSync: async (data: ChatRequest) => {
    if (USE_MOCK_API) {
      // Collect all chunks from mock stream
      const chunks: string[] = [];
      for await (const chunk of mockStreamChatResponse(data.question, data.knowledge_base_id?.toString())) {
        chunks.push(chunk);
      }

      return {
        code: 0,
        message: 'success',
        data: {
          answer: chunks.join(''),
          sources: [],
        },
      } as any;
    }

    return apiClient.post<BaseResponse<ChatResponse>>('/api/v1/chat', data);
  },

  /**
   * Disconnect Socket.IO connection
   */
  disconnect: () => {
    if (socketIOClient) {
      socketIOClient.disconnect();
      socketIOClient = null;
      connectionPromise = null;
    }
  },
};
