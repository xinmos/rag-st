export type DocumentStatus = 'processing' | 'completed' | 'failed';

export interface Document {
  id: number;
  knowledge_base_id: number;
  file_name: string;
  file_size: number;
  file_type: string;
  status: DocumentStatus;
  progress: number;
  chunk_count?: number;
  error_message?: string;
  created_at: string;
}

export interface DocumentUploadResponse {
  document_id: number;
  status: string;
}
