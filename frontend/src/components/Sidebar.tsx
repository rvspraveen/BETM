import React, { useState } from 'react';
import {
  MessageSquare, BarChart2, BookOpen, CheckSquare,
  Zap, Settings, ChevronLeft, ChevronRight, Moon, Sun,
  Plus, Search, Trash2,
  type LucideIcon,
} from 'lucide-react';
import type { InvestigationThread, ViewType } from '../types';

interface SidebarProps {
  activeView: ViewType;
  onViewChange: (v: ViewType) => void;
  pendingReviewCount: number;
  darkMode: boolean;
  onToggleDark: () => void;
  chatThreads: InvestigationThread[];
  activeThreadId: string | null;
  onNewThread: () => void;
  onThreadSelect: (threadId: string) => void;
  onThreadDelete: (threadId: string) => void;
}

const NAV_ITEMS: { id: ViewType; label: string; Icon: LucideIcon }[] = [
  { id: 'investigation', label: 'Investigation', Icon: MessageSquare },
  { id: 'analytics',     label: 'Analytics',     Icon: BarChart2     },
  { id: 'positions',     label: 'Positions',      Icon: BookOpen      },
  { id: 'review',        label: 'Review Queue',   Icon: CheckSquare   },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeView, onViewChange, pendingReviewCount, darkMode, onToggleDark,
  chatThreads, activeThreadId, onNewThread, onThreadSelect, onThreadDelete,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [threadSearch, setThreadSearch] = useState('');
  const filteredThreads = chatThreads.filter(thread =>
    thread.title.toLowerCase().includes(threadSearch.trim().toLowerCase())
  );

  return (
    <aside
      className={`
        shrink-0 flex flex-col bg-base-200 border-r border-base-300
        transition-all duration-200
        ${collapsed ? 'w-14' : 'w-56'}
      `}
    >
      {/* Logo */}
      <div className="h-12 flex items-center px-3 border-b border-base-300 gap-2 shrink-0">
        <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center shrink-0">
          <Zap size={15} className="text-primary" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <p className="text-xs font-bold text-base-content leading-tight">ERCOT Copilot</p>
            <p className="text-[10px] text-base-content/40 leading-tight">AI Market Intel</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(c => !c)}
          className="ml-auto btn btn-ghost btn-xs px-1 text-base-content/40 hover:text-base-content"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
        </button>
      </div>

      {/* Nav */}
      <nav className="shrink-0 py-3 space-y-0.5 px-1.5">
        {!collapsed && (
          <p className="px-2 pb-1.5 text-[10px] uppercase tracking-widest text-base-content/30 font-semibold">
            Navigation
          </p>
        )}
        {NAV_ITEMS.map(({ id, label, Icon }) => {
          const active = id === activeView;
          const isReview = id === 'review';
          return (
            <button
              key={id}
              onClick={() => onViewChange(id)}
              title={collapsed ? label : undefined}
              className={`
                w-full flex items-center gap-2.5 px-2 py-2 rounded-lg text-left
                transition-all duration-150 text-sm font-medium group relative
                ${active
                  ? 'bg-primary/15 text-primary'
                  : 'text-base-content/60 hover:bg-base-300 hover:text-base-content'}
              `}
            >
              <Icon size={16} className={`shrink-0 ${active ? 'text-primary' : 'group-hover:text-base-content'}`} />
              {!collapsed && <span className="truncate">{label}</span>}
              {isReview && pendingReviewCount > 0 && (
                <span className={`
                  ml-auto shrink-0 min-w-[18px] h-[18px] rounded-full flex items-center justify-center
                  text-[10px] font-bold bg-error text-error-content
                  ${collapsed ? 'absolute top-1 right-1' : ''}
                `}>
                  {pendingReviewCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Threads */}
      <section className="flex-1 min-h-0 border-t border-base-300 px-1.5 py-2 overflow-hidden">
        <button
          onClick={onNewThread}
          title="New chat"
          className={`
            w-full flex items-center gap-2 px-2 py-2 rounded-lg text-left text-sm font-semibold
            bg-base-100 text-base-content hover:bg-base-300 transition-colors
            ${collapsed ? 'justify-center' : ''}
          `}
        >
          <Plus size={16} className="shrink-0" />
          {!collapsed && <span>New Chat</span>}
        </button>

        {!collapsed && (
          <div className="mt-3 flex h-[calc(100%-44px)] min-h-0 flex-col">
            <div className="flex items-center gap-2 px-2 pb-2 text-xs font-semibold text-base-content/70">
              <MessageSquare size={14} className="shrink-0" />
              <span>Threads</span>
            </div>

            <label className="mb-2 flex items-center gap-2 rounded-lg bg-base-300/50 px-2 py-2 text-xs text-base-content/40">
              <Search size={14} className="shrink-0" />
              <input
                value={threadSearch}
                onChange={e => setThreadSearch(e.target.value)}
                placeholder="Search threads"
                className="min-w-0 flex-1 bg-transparent text-base-content outline-none placeholder:text-base-content/35"
              />
            </label>

            <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto pr-0.5">
              {filteredThreads.map(thread => {
                const active = activeView === 'investigation' && thread.id === activeThreadId;
                return (
                  <div
                    key={thread.id}
                    title={thread.title}
                    className={`
                      group flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-xs
                      transition-colors
                      ${active
                        ? 'bg-primary/15 text-base-content'
                        : 'text-base-content/60 hover:bg-base-300 hover:text-base-content'}
                    `}
                  >
                    <button
                      onClick={() => onThreadSelect(thread.id)}
                      className="flex min-w-0 flex-1 items-center gap-2 text-left"
                    >
                      <MessageSquare size={13} className={`shrink-0 ${active ? 'text-primary' : 'text-base-content/35'}`} />
                      <span className="min-w-0 flex-1 truncate">{thread.title || 'Untitled chat'}</span>
                    </button>
                    <button
                      onClick={(event) => {
                        event.stopPropagation();
                        onThreadDelete(thread.id);
                      }}
                      title="Delete thread"
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-base-content/35 opacity-0 transition-all hover:bg-error/15 hover:text-error group-hover:opacity-100"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })}

              {chatThreads.length === 0 && (
                <p className="px-2 py-2 text-xs text-base-content/35">
                  No threads yet
                </p>
              )}
              {chatThreads.length > 0 && filteredThreads.length === 0 && (
                <p className="px-2 py-2 text-xs text-base-content/35">
                  No matching threads
                </p>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Bottom */}
      <div className="shrink-0 border-t border-base-300 p-2 space-y-1">
        {/* Connection status */}
        {!collapsed && (
          <div className="px-2 py-1.5 rounded-lg bg-base-300/50 space-y-1 mb-1">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-success shrink-0" />
              <span className="text-[10px] text-base-content/50">GPT-4o</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-success shrink-0" />
              <span className="text-[10px] text-base-content/50">pgvector</span>
            </div>
          </div>
        )}

        {/* Dark/light toggle */}
        <button
          onClick={onToggleDark}
          title="Toggle theme"
          className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-base-content/50
                     hover:bg-base-300 hover:text-base-content transition-colors text-xs"
        >
          {darkMode ? <Sun size={14} className="shrink-0" /> : <Moon size={14} className="shrink-0" />}
          {!collapsed && <span>{darkMode ? 'Light mode' : 'Dark mode'}</span>}
        </button>

        {/* Settings */}
        <button
          title="Settings"
          className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-base-content/50
                     hover:bg-base-300 hover:text-base-content transition-colors text-xs"
        >
          <Settings size={14} className="shrink-0" />
          {!collapsed && <span>Settings</span>}
        </button>
      </div>
    </aside>
  );
};
