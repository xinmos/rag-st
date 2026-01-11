'use client';

import { useEffect, useRef, useState } from 'react';
import { Send, StopCircle, Sparkles, Trash2, Copy, Check } from 'lucide-react';
import { useChat } from '@/lib/hooks/useChat';
import { useKnowledgeBases } from '@/lib/hooks/useKnowledgeBases';
import ReactMarkdown, { Components } from 'react-markdown';

interface ChatInterfaceProps {
  knowledgeBaseId?: number;
}

export function ChatInterface({ knowledgeBaseId }: ChatInterfaceProps) {
  const { messages, isStreaming, sendMessage, clearChat } = useChat();
  const { knowledgeBases } = useKnowledgeBases({ pageSize: 100 });
  const [input, setInput] = useState('');

  // 从localStorage读取上次选择的知识库ID
  const getInitialKBId = (): number | undefined => {
    if (typeof window === 'undefined') return undefined;
    const savedKBId = localStorage.getItem('selected_knowledge_base_id');
    return savedKBId ? parseInt(savedKBId, 10) : undefined;
  };

  const [selectedKBId, setSelectedKBId] = useState<number | undefined>(() => {
    return knowledgeBaseId || getInitialKBId();
  });

  // 当知识库列表加载完成或URL参数变化时，更新选中的知识库ID
  useEffect(() => {
    if (knowledgeBaseId) {
      // 如果URL传入了knowledgeBaseId，使用它并保存
      setSelectedKBId(knowledgeBaseId);
      localStorage.setItem('selected_knowledge_base_id', String(knowledgeBaseId));
    } else if (knowledgeBases.length > 0 && !selectedKBId) {
      // 如果没有URL参数，也没有选中的，从localStorage恢复或选择第一个
      const savedKBId = getInitialKBId();
      if (savedKBId && knowledgeBases.some(kb => kb.id === savedKBId)) {
        setSelectedKBId(savedKBId);
      } else {
        // 选择第一个并保存
        setSelectedKBId(knowledgeBases[0].id);
        localStorage.setItem('selected_knowledge_base_id', String(knowledgeBases[0].id));
      }
    }
  }, [knowledgeBaseId, knowledgeBases]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const messageToSend = input;
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    await sendMessage(messageToSend, selectedKBId);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  };

  const handleCopy = (content: string, id: number) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-slate-50 to-sky-50/30">
      {/* Header */}
      <div className="border-b border-slate-200/60 bg-white/80 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-sky-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-slate-800">AI 问答</h1>
                <p className="text-sm text-slate-500">
                  {selectedKBId ? '基于知识库的智能对话' : '通用对话模式'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <select
                value={selectedKBId || ''}
                onChange={(e) => {
                  const newKBId = e.target.value ? Number(e.target.value) : undefined;
                  setSelectedKBId(newKBId);
                  // 保存到localStorage
                  if (newKBId) {
                    localStorage.setItem('selected_knowledge_base_id', String(newKBId));
                  } else {
                    localStorage.removeItem('selected_knowledge_base_id');
                  }
                }}
                className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 border-0 text-sm text-slate-700 cursor-pointer transition-colors"
              >
                <option value="">选择知识库</option>
                {knowledgeBases.map((kb) => (
                  <option key={kb.id} value={kb.id}>
                    {kb.name}
                  </option>
                ))}
              </select>

              <button
                onClick={clearChat}
                disabled={messages.length === 0}
                className="p-2 rounded-lg hover:bg-slate-200 text-slate-600 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                title="清空对话"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 py-6">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-teal-400 to-sky-500 flex items-center justify-center shadow-xl shadow-teal-500/20">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-2xl font-semibold text-slate-800 mb-2">开始你的对话</h2>
                <p className="text-slate-500">选择知识库，提出问题，获取智能答案</p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message, index) => (
                <div
                  key={message.id}
                  className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-sky-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                  )}

                  <div
                    className={`flex-1 max-w-[80%] ${
                      message.role === 'user' ? 'flex flex-col items-end' : ''
                    }`}
                  >
                    <div
                      className={`relative ${
                        message.role === 'user'
                          ? 'bg-gradient-to-br from-sky-500 to-teal-500 text-white rounded-2xl rounded-tr-sm px-5 py-3 shadow-lg shadow-sky-500/20'
                          : 'bg-white text-slate-700 rounded-2xl rounded-tl-sm px-5 py-3 shadow-md border border-slate-100'
                      }`}
                    >
                      {message.role === 'assistant' ? (
                        <div className="markdown-content">
                          <ReactMarkdown
                            components={{
                              p: ({ children }) => {
                                // 检查是否包含代码块（pre 元素），如果有则不包裹 p 标签
                                const hasPre = (children as any)?.some?.(
                                  (child: any) => child?.type === 'pre'
                                );
                                if (hasPre) {
                                  return <>{children}</>;
                                }
                                return <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>;
                              },
                              code: ({ inline, className, children }: any) => {
                                const match = /language-(\w+)/.exec(className || '');
                                return !inline ? (
                                  <pre className="bg-slate-100 text-slate-800 p-4 rounded-lg overflow-x-auto my-3 font-mono text-[13px] leading-relaxed border border-slate-300">
                                    <code className="text-slate-800">{String(children).replace(/\n$/, '')}</code>
                                  </pre>
                                ) : (
                                  <code className="px-1.5 py-0.5 rounded bg-slate-200 text-red-600 font-mono text-sm font-semibold">
                                    {children}
                                  </code>
                                );
                              },
                              ul: ({ children }) => (
                                <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>
                              ),
                              ol: ({ children }) => (
                                <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>
                              ),
                              h1: ({ children }) => (
                                <h1 className="text-xl font-bold mb-3 text-slate-800">{children}</h1>
                              ),
                              h2: ({ children }) => (
                                <h2 className="text-lg font-bold mb-3 text-slate-800">{children}</h2>
                              ),
                              h3: ({ children }) => (
                                <h3 className="text-base font-bold mb-3 text-slate-800">{children}</h3>
                              ),
                              blockquote: ({ children }) => (
                                <blockquote className="border-l-4 border-teal-400 pl-4 italic my-3 text-slate-600">
                                  {children}
                                </blockquote>
                              ),
                            }}
                          >
                            {message.content || '思考中...'}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                      )}
                    </div>

                    {message.role === 'assistant' && (
                      <div className="mt-2 flex items-center gap-2 ml-1">
                        <button
                          onClick={() => handleCopy(message.content, message.id)}
                          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition-colors px-2 py-1 rounded hover:bg-slate-100"
                        >
                          {copiedId === message.id ? (
                            <>
                              <Check className="w-3.5 h-3.5" />
                              已复制
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              复制
                            </>
                          )}
                        </button>
                        {message.timestamp && (
                          <span className="text-xs text-slate-400">
                            {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        )}
                      </div>
                    )}

                    {message.references && message.references.length > 0 && (
                      <details className="mt-2 group">
                        <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-700 transition-colors select-none">
                          <span className="inline-flex items-center gap-1.5">
                            <span className="font-medium">参考来源</span>
                            <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-600 text-xs">
                              {message.references.length}
                            </span>
                          </span>
                        </summary>
                        <div className="mt-2 space-y-2 ml-1">
                          {message.references.map((ref, idx) => (
                            <div
                              key={idx}
                              className="p-3 rounded-lg bg-slate-50 border border-slate-200 hover:border-teal-300 transition-colors"
                            >
                              <div className="font-medium text-sm text-slate-800 mb-1">
                                {ref.document_name}
                              </div>
                              <div className="text-xs text-slate-500 mb-2">页码: {ref.page}</div>
                              <p className="text-sm text-slate-600 line-clamp-2">{ref.content}</p>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>

                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-teal-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  )}
                </div>
              ))}

              {isStreaming && (
                <div className="flex gap-4 justify-start">
                  <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-sky-500 flex items-center justify-center shadow-lg shadow-teal-500/20 animate-pulse">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-white rounded-2xl rounded-tl-sm px-5 py-4 shadow-md border border-slate-100">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce"></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-200/60 bg-white/80 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder="输入你的问题... (Shift+Enter 换行)"
                disabled={isStreaming}
                rows={1}
                className="w-full px-4 py-3 pr-14 rounded-xl bg-slate-100 hover:bg-slate-200/80 focus:bg-white focus:ring-2 focus:ring-teal-500/50 border-0 resize-none transition-all text-slate-800 placeholder:text-slate-400 disabled:opacity-50"
                style={{ minHeight: '48px', maxHeight: '200px' }}
              />
              <div className="absolute right-3 bottom-3">
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isStreaming}
                  className="p-2 rounded-lg bg-gradient-to-br from-teal-400 to-sky-500 hover:from-teal-500 hover:to-sky-600 text-white shadow-lg shadow-teal-500/20 disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95"
                  title="发送"
                >
                  {isStreaming ? (
                    <StopCircle className="w-5 h-5" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx global>{`
        .markdown-content pre {
          margin: 0.75rem 0;
          tab-size: 4;
        }
        .markdown-content pre code {
          font-family: 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
          letter-spacing: 0.01em;
        }
      `}</style>
    </div>
  );
}
