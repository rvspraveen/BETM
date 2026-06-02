/**
 * Investigation View — AI chat interface with real SSE streaming.
 * Connects to POST /api/v1/investigate when VITE_MOCK_MODE=false.
 * Falls back to mock stream when VITE_MOCK_MODE=true.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Activity,
  FileText,
  GitMerge,
  Mic,
  Paperclip,
  Search,
  Send,
  ShieldAlert,
  Square,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { streamInvestigation, SSEEvent } from '../services/api';
import { QUERY_CAPABILITY_GROUPS } from '../data/mockData';
import { ResponseVisualizations } from './ResponseVisualizations';
import type {
  InvestigationMessage,
  InvestigationThread,
  QueryCategory,
  QueryChip,
} from '../types';

// ── Types ─────────────────────────────────────────────────────────────────────

type Message = InvestigationMessage;

interface InvestigationViewProps {
  threads: InvestigationThread[];
  activeThreadId: string | null;
  onThreadsChange: React.Dispatch<React.SetStateAction<InvestigationThread[]>>;
  onActiveThreadChange: (threadId: string | null) => void;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function genId() {
  return Math.random().toString(36).slice(2, 10);
}

function createThreadTitle(query: string) {
  const normalized = query.replace(/\s+/g, ' ').trim();
  return normalized.length > 48 ? `${normalized.slice(0, 45)}...` : normalized;
}

function sortThreads(threads: InvestigationThread[]) {
  return [...threads].sort((a, b) => b.updatedAt - a.updatedAt);
}

const STEP_LABELS: Record<string, string> = {
  classifier: 'Intent Classification',
  entity_extractor: 'Entity Extraction',
  retriever: 'Document Retrieval',
  analytics: 'Quantitative Analysis',
  synthesizer: 'Answer Synthesis',
  confidence_check: 'Confidence Assessment',
};

const CATEGORY_ICONS: Record<QueryCategory, LucideIcon> = {
  market: Activity,
  exposure: ShieldAlert,
  rules: FileText,
  hybrid: GitMerge,
};

// ── Markdown-ish renderer (lightweight, no dep) ───────────────────────────────

function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const nodes: React.ReactNode[] = [];
  let inTable = false;
  let tableRows: string[][] = [];

  const flushTable = () => {
    if (!tableRows.length) return;
    const [header, , ...body] = tableRows;
    nodes.push(
      <div key={`tbl-${nodes.length}`} className="overflow-x-auto my-3">
        <table className="table table-xs table-zebra w-full text-sm">
          <thead>
            <tr>{(header ?? []).map((h, i) => <th key={i}>{h.trim()}</th>)}</tr>
          </thead>
          <tbody>
            {body.map((row, ri) => (
              <tr key={ri}>{row.map((c, ci) => <td key={ci}>{c.trim()}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableRows = [];
    inTable = false;
  };

  lines.forEach((line, i) => {
    if (line.startsWith('|')) {
      inTable = true;
      tableRows.push(line.split('|').filter(Boolean));
      return;
    }
    if (inTable) flushTable();

    if (line.startsWith('### ')) {
      nodes.push(<h3 key={i} className="text-base font-bold mt-4 mb-1">{line.slice(4)}</h3>);
    } else if (line.startsWith('## ')) {
      nodes.push(<h2 key={i} className="text-lg font-bold mt-4 mb-1">{line.slice(3)}</h2>);
    } else if (line.startsWith('# ')) {
      nodes.push(<h1 key={i} className="text-xl font-bold mt-2 mb-2">{line.slice(2)}</h1>);
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      nodes.push(
        <li key={i} className="ml-4 list-disc" dangerouslySetInnerHTML={{ __html: inlineMd(line.slice(2)) }} />
      );
    } else if (line.match(/^\d+\. /)) {
      nodes.push(
        <li key={i} className="ml-4 list-decimal" dangerouslySetInnerHTML={{ __html: inlineMd(line.replace(/^\d+\. /, '')) }} />
      );
    } else if (line.trim() === '') {
      nodes.push(<br key={i} />);
    } else {
      nodes.push(
        <p key={i} className="my-1 leading-relaxed" dangerouslySetInnerHTML={{ __html: inlineMd(line) }} />
      );
    }
  });
  if (inTable) flushTable();
  return nodes;
}

function inlineMd(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code class="bg-base-300 px-1 rounded text-xs">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="link link-primary" target="_blank">$1</a>');
}

// ── Message Card ──────────────────────────────────────────────────────────────

function MessageCard({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';
  const hasVisualizations = !isUser && Boolean(msg.visualizations?.length);
  const bubbleWidth = isUser
    ? 'max-w-[80%]'
    : hasVisualizations
      ? 'max-w-[92%] xl:max-w-[980px]'
      : 'max-w-[80%]';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-4`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-sm font-bold
        ${isUser ? 'bg-primary text-primary-content' : 'bg-secondary/20 text-secondary'}`}>
        {isUser ? 'U' : <Zap size={14} />}
      </div>

      {/* Bubble */}
      <div className={`${bubbleWidth} rounded-2xl px-4 py-3 text-sm
        ${isUser
          ? 'bg-primary text-primary-content rounded-tr-sm'
          : 'bg-base-200 rounded-tl-sm'}`}>

        {/* Reasoning trace — inline streaming steps */}
        {!isUser && msg.reasoning && msg.reasoning.length > 0 && (
          <details className="mb-3 text-xs opacity-60 group" open={msg.streaming}>
            <summary className="cursor-pointer font-medium hover:opacity-80 select-none">
              🧠 Reasoning trace — {msg.reasoning.length} steps
            </summary>
            <div className="mt-1 space-y-0.5 pl-3 border-l border-base-content/20">
              {msg.reasoning.map((r, i) => (
                <div key={i} className="text-base-content/50">
                  <span className="font-semibold text-base-content/70">{r.step}: </span>
                  <span dangerouslySetInnerHTML={{ __html: inlineMd(r.content) }} />
                </div>
              ))}
              {msg.streaming && <div className="animate-pulse">…</div>}
            </div>
          </details>
        )}

        {/* Streaming cursor */}
        {msg.streaming && !msg.content && (
          <div className="flex gap-1 items-center py-2">
            <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:0ms]" />
            <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:150ms]" />
            <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:300ms]" />
          </div>
        )}

        {/* Answer content */}
        {msg.content && (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {renderMarkdown(msg.content)}
            {msg.streaming && <span className="inline-block w-0.5 h-4 bg-current animate-pulse ml-0.5 align-middle" />}
          </div>
        )}

        {/* Structured response visualizations */}
        {!isUser && msg.visualizations && msg.visualizations.length > 0 && (
          <ResponseVisualizations items={msg.visualizations} />
        )}

        {/* Error */}
        {msg.error && (
          <p className="text-error text-xs mt-1">⚠️ {msg.content}</p>
        )}

        {/* Sources */}
        {!isUser && msg.sources && msg.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-base-300">
            <p className="text-xs opacity-60 mb-2">Sources</p>
            <div className="flex flex-wrap gap-1">
              {msg.sources.map(src => (
                <span key={src.id} className="badge badge-sm badge-ghost gap-1" title={src.excerpt}>
                  {src.source_type === 'document' ? '📄' : '📊'}
                  <span className="truncate max-w-[180px]">{src.title}</span>
                  <span className="opacity-50">{(src.relevance_score * 100).toFixed(0)}%</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Footer metadata */}
        {!isUser && (msg.confidence !== undefined || msg.latency_ms !== undefined || msg.escalated) && (
          <div className="flex gap-3 mt-2 text-xs opacity-50 flex-wrap">
            {msg.confidence !== undefined && (
              <span className={msg.confidence < 0.72 ? 'text-warning' : 'text-success'}>
                Confidence: {(msg.confidence * 100).toFixed(0)}%
              </span>
            )}
            {msg.latency_ms && <span>{(msg.latency_ms / 1000).toFixed(1)}s</span>}
            {msg.escalated && <span className="text-warning font-medium">⚠ Sent to review queue</span>}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Home Surface ─────────────────────────────────────────────────────────────

interface HomeSurfaceProps {
  input: string;
  isStreaming: boolean;
  activeCategory: QueryCategory | null;
  inputRef: React.RefObject<HTMLTextAreaElement>;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  onCategoryChange: (category: QueryCategory) => void;
  onSelectQuery: (chip: QueryChip) => void;
}

function IconButton({
  title,
  children,
  disabled,
}: {
  title: string;
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      title={title}
      disabled={disabled}
      className="flex h-9 w-9 items-center justify-center rounded-lg bg-base-300/70 text-base-content/65 transition-colors hover:bg-base-300 hover:text-base-content disabled:cursor-not-allowed disabled:opacity-40"
    >
      {children}
    </button>
  );
}

function HomeSurface({
  input,
  isStreaming,
  activeCategory,
  inputRef,
  onInputChange,
  onSubmit,
  onCategoryChange,
  onSelectQuery,
}: HomeSurfaceProps) {
  const selectedGroup =
    QUERY_CAPABILITY_GROUPS.find(group => group.id === activeCategory) ?? null;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-5 py-8">
      <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col items-center justify-center gap-7">
        <form
          onSubmit={e => {
            e.preventDefault();
            onSubmit();
          }}
          className="w-full max-w-4xl rounded-2xl border border-base-content/10 bg-base-100 shadow-lg shadow-black/5"
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            rows={2}
            placeholder="Ask, research, think anything"
            className="min-h-[86px] w-full resize-none bg-transparent px-5 pt-5 text-lg leading-7 text-base-content outline-none placeholder:text-base-content/35 disabled:cursor-not-allowed"
          />
          <div className="flex items-center justify-between gap-3 px-3 pb-3">
            <div className="flex items-center gap-2">
              <IconButton title="Attach context" disabled={isStreaming}>
                <Paperclip size={18} />
              </IconButton>
              <IconButton title="Search market data" disabled={isStreaming}>
                <Search size={18} />
              </IconButton>
            </div>
            <div className="flex items-center gap-2">
              <IconButton title="Voice input" disabled={isStreaming}>
                <Mic size={18} />
              </IconButton>
              <button
                type="submit"
                title="Send"
                disabled={!input.trim() || isStreaming}
                className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-content transition-colors hover:bg-primary/85 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </form>

        <div className="fade-up w-full max-w-5xl space-y-3">
          <div
            role="tablist"
            aria-label="Query categories"
            className="grid grid-cols-1 gap-2 rounded-xl border border-base-content/10 bg-base-200/80 p-2 shadow-sm shadow-black/5 sm:grid-cols-2 xl:grid-cols-4"
          >
            {QUERY_CAPABILITY_GROUPS.map(group => {
              const Icon = CATEGORY_ICONS[group.id];
              const active = group.id === selectedGroup?.id;
              return (
                <button
                  key={group.id}
                  role="tab"
                  aria-selected={active}
                  onClick={() => onCategoryChange(group.id)}
                  className={`
                    flex h-14 min-w-0 items-center gap-3 rounded-lg px-3 text-left text-sm font-semibold
                    outline-none transition-all duration-150 focus-visible:ring-2 focus-visible:ring-primary/60
                    ${active
                      ? 'bg-base-100 text-base-content shadow-sm ring-1 ring-base-content/10'
                      : 'text-base-content/55 hover:bg-base-300/70 hover:text-base-content/80'}
                  `}
                >
                  <span className={`
                    flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors
                    ${active ? group.bg : 'bg-base-300/70'}
                  `}>
                    <Icon size={17} className={active ? group.color : 'text-base-content/45'} />
                  </span>
                  <span className="min-w-0 truncate">{group.label}</span>
                </button>
              );
            })}
          </div>

          {selectedGroup && (
            <div className="fade-up rounded-xl border border-base-content/10 bg-base-200/75 p-4 shadow-sm shadow-black/5">
              <p className={`mb-3 text-sm font-semibold ${selectedGroup.color}`}>
                {selectedGroup.tagline}
              </p>
              <div className="space-y-2">
                {selectedGroup.queries.map((chip, index) => (
                  <button
                    key={chip.text}
                    onClick={() => onSelectQuery(chip)}
                    disabled={isStreaming}
                    className={`
                      group flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left
                      text-sm text-base-content/75 transition-colors
                      hover:bg-base-300/70 hover:text-base-content disabled:cursor-not-allowed disabled:opacity-45
                      ${selectedGroup.border}
                    `}
                  >
                    <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${selectedGroup.bg} ${selectedGroup.color}`}>
                      {index + 1}
                    </span>
                    <span className="min-w-0 flex-1 leading-relaxed">{chip.text}</span>
                    <Send size={15} className={`${selectedGroup.color} opacity-0 transition-opacity group-hover:opacity-100`} />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function InvestigationView({
  threads,
  activeThreadId,
  onThreadsChange,
  onActiveThreadChange,
}: InvestigationViewProps) {
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeCategory, setActiveCategory] = useState<QueryCategory | null>(null);
  const stopRef = useRef<(() => void) | null>(null);
  const streamingThreadIdRef = useRef<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const activeThread = threads.find(thread => thread.id === activeThreadId) ?? null;
  const messages = activeThread?.messages ?? [];
  const hasConversation = messages.length > 0;

  // Auto-scroll
  useEffect(() => {
    if (hasConversation) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activeThreadId, hasConversation, messages]);

  const sendMessage = useCallback(async (text?: string) => {
    const query = (text ?? input).trim();
    if (!query || isStreaming) return;
    setInput('');

    const userMsg: Message = { id: genId(), role: 'user', content: query };
    const assistantId = genId();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      reasoning: [],
      streaming: true,
    };
    const now = Date.now();
    const threadId = activeThread?.id ?? genId();

    onActiveThreadChange(threadId);
    onThreadsChange(prev => {
      const existing = prev.find(thread => thread.id === threadId);
      if (!existing) {
        return sortThreads([
          {
            id: threadId,
            title: createThreadTitle(query),
            messages: [userMsg, assistantMsg],
            createdAt: now,
            updatedAt: now,
          },
          ...prev,
        ]);
      }

      return sortThreads(prev.map(thread =>
        thread.id === threadId
          ? {
              ...thread,
              title: thread.title || createThreadTitle(query),
              messages: [...thread.messages, userMsg, assistantMsg],
              updatedAt: now,
            }
          : thread
      ));
    });
    setIsStreaming(true);
    streamingThreadIdRef.current = threadId;

    const stop = streamInvestigation({ query, session_id: threadId }, (event: SSEEvent) => {
      onThreadsChange(prev => sortThreads(prev.map(thread => {
        if (thread.id !== threadId) return thread;

        return {
          ...thread,
          updatedAt: Date.now(),
          messages: thread.messages.map(message => {
            if (message.id !== assistantId) return message;

            switch (event.type) {
              case 'status':
                return {
                  ...message,
                  reasoning: [
                    ...(message.reasoning ?? []),
                    { step: STEP_LABELS[event.step] ?? event.step, content: event.content, done: false },
                  ],
                };

              case 'token':
                return { ...message, content: message.content + (event.content ?? '') };

              case 'metadata':
                return {
                  ...message,
                  sources: event.sources,
                  confidence: event.confidence,
                  escalated: event.escalated,
                  intent: event.intent,
                  visualizations: event.visualizations,
                  latency_ms: event.latency_ms,
                };

              case 'error':
                return { ...message, content: event.content, error: true, streaming: false };

              case 'done':
                return { ...message, streaming: false };

              default:
                return message;
            }
          }),
        };
      })));

      if (event.type === 'done' || event.type === 'error') {
        setIsStreaming(false);
        stopRef.current = null;
        streamingThreadIdRef.current = null;
      }
    });

    stopRef.current = stop;
  }, [
    activeThread,
    input,
    isStreaming,
    onActiveThreadChange,
    onThreadsChange,
  ]);

  const handleStop = () => {
    const threadId = streamingThreadIdRef.current;
    stopRef.current?.();
    stopRef.current = null;
    streamingThreadIdRef.current = null;
    setIsStreaming(false);

    if (!threadId) return;
    onThreadsChange(prev => sortThreads(prev.map(thread =>
      thread.id === threadId
        ? {
            ...thread,
            updatedAt: Date.now(),
            messages: thread.messages.map(message =>
              message.streaming
                ? { ...message, streaming: false, content: message.content || '*(stopped)*' }
                : message
            ),
          }
        : thread
    )));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSelectQuery = (chip: QueryChip) => {
    sendMessage(chip.text);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-base-300 px-6 py-4">
        <Zap size={18} className="text-primary" />
        <h1 className="text-lg font-semibold">Investigation</h1>
        <div className="ml-auto flex items-center gap-2 text-xs opacity-50">
          <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
          {(import.meta as ImportMeta).env.VITE_MOCK_MODE === 'true' ? 'Mock mode' : 'Live'}
        </div>
      </div>

      {!hasConversation ? (
        <HomeSurface
          input={input}
          isStreaming={isStreaming}
          activeCategory={activeCategory}
          inputRef={inputRef}
          onInputChange={setInput}
          onSubmit={() => sendMessage()}
          onCategoryChange={setActiveCategory}
          onSelectQuery={handleSelectQuery}
        />
      ) : (
        <>
          {/* Messages */}
          <div className="flex-1 space-y-2 overflow-y-auto px-5 py-5">
            {messages.map(msg => (
              <MessageCard key={msg.id} msg={msg} />
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="border-t border-base-300 px-5 pb-4 pt-3">
            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                className="textarea textarea-bordered min-h-[48px] max-h-[160px] flex-1 resize-none text-sm"
                placeholder="Ask about prices, congestion, settlements, positions... (Shift+Enter for new line)"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={isStreaming}
              />
              {isStreaming ? (
                <button className="btn btn-square btn-error btn-sm" onClick={handleStop} title="Stop">
                  <Square size={16} />
                </button>
              ) : (
                <button
                  className="btn btn-square btn-primary btn-sm"
                  onClick={() => sendMessage()}
                  disabled={!input.trim()}
                  title="Send (Enter)"
                >
                  <Send size={16} />
                </button>
              )}
            </div>
            <p className="mt-1 pl-1 text-xs opacity-40">
              {isStreaming ? 'Streaming response...' : 'Enter to send / Shift+Enter for new line'}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
