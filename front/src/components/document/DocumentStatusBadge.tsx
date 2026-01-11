'use client';

import { Badge } from 'antd';
import type { DocumentStatus } from '@/lib/types';

interface DocumentStatusBadgeProps {
  status: DocumentStatus;
}

const statusConfig: Record<
  DocumentStatus,
  { text: string; status: 'success' | 'processing' | 'error' | 'default' }
> = {
  processing: { text: '处理中', status: 'processing' },
  completed: { text: '已完成', status: 'success' },
  failed: { text: '失败', status: 'error' },
};

export function DocumentStatusBadge({ status }: DocumentStatusBadgeProps) {
  const config = statusConfig[status];
  return <Badge status={config.status} text={config.text} />;
}
