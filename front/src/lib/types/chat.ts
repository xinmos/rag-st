export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: number;
  role: MessageRole;
  content: string;
  timestamp: string;
  references?: Reference[];
}

export interface Reference {
  document_id: number;
  document_name: string;
  page: number;
  content: string;
  score?: number;
}

export interface ChatRequest {
  question: string;
  knowledge_base_id?: number;
  session_id?: string;
}

export interface ChatResponse {
  answer: string;
  references: Reference[];
}
