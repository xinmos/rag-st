import { KnowledgeBase, Document, ChatResponse, ChatMessage } from '../types';

// Mock Knowledge Bases
export const mockKnowledgeBases: KnowledgeBase[] = [
  {
    id: 1,
    name: '产品文档',
    description: '公司产品相关文档和手册',
    document_count: 25,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-10T00:00:00Z',
  },
  {
    id: 2,
    name: '技术文档',
    description: '开发规范、API文档等',
    document_count: 42,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-09T00:00:00Z',
  },
  {
    id: 3,
    name: 'HR 政策',
    description: '公司人事政策、员工手册',
    document_count: 15,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-08T00:00:00Z',
  },
];

// Mock Documents
export const mockDocuments: Document[] = [
  {
    id: 1,
    knowledge_base_id: 1,
    file_name: '产品介绍.pdf',
    file_size: 1024000,
    file_type: 'application/pdf',
    status: 'completed',
    created_at: '2024-01-01T00:00:00Z',
    progress: 100,
  },
  {
    id: 2,
    knowledge_base_id: 1,
    file_name: '用户手册.docx',
    file_size: 512000,
    file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    status: 'completed',
    created_at: '2024-01-02T00:00:00Z',
    progress: 100,
  },
  {
    id: 3,
    knowledge_base_id: 1,
    file_name: '快速入门.txt',
    file_size: 5120,
    file_type: 'text/plain',
    status: 'processing',
    created_at: '2024-01-03T00:00:00Z',
    progress: 45,
  },
];

// Mock Chat Response Generator
export function mockChatResponse(question: string, kbId?: string): ChatResponse {
  return {
    answer: `这是对"${question}"的模拟回答。\n\n当后端RAG API完成后，这里将显示基于知识库的AI回答。\n\n## 回答内容\n\n这是一个Markdown格式的回答示例。在实际系统中，AI会根据知识库中的文档内容生成详细的回答。\n\n### 关键点\n1. 回答会基于知识库中的相关文档\n2. 会引用具体的文档来源\n3. 支持Markdown格式的富文本`,
    references: [
      {
        document_id: 1,
        document_name: '产品介绍.pdf',
        page: 3,
        content: '相关文档片段：这里会显示来自知识库文档的具体内容片段...',
        score: 0.95,
      },
      {
        document_id: 2,
        document_name: '用户手册.docx',
        page: 15,
        content: '另一段相关文档内容...',
        score: 0.87,
      },
    ],
  };
}

// Mock streaming chat generator
export async function* mockStreamChatResponse(
  question: string,
  kbId?: string
): AsyncGenerator<string, void, unknown> {
  const response = mockChatResponse(question, kbId);
  const chunks = response.answer.match(/.{1,15}/g) || [];

  for (const chunk of chunks) {
    await new Promise((resolve) => setTimeout(resolve, 50));
    yield chunk;
  }
}
