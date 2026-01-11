'use client';

import { useParams } from 'next/navigation';
import { ChatInterface } from '@/components/chat/ChatInterface';

export default function ChatWithKBPage() {
  const params = useParams();
  const knowledgeBaseId = params.id ? Number(params.id) : undefined;

  return <ChatInterface knowledgeBaseId={knowledgeBaseId} />;
}
