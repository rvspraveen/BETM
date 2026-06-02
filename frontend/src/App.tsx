/**
 * ERCOT Copilot — Root App Component
 * Polls review count from /api/v1/reviews/count every 60s when live.
 */
import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import InvestigationView from './components/InvestigationView';
import { AnalyticsView } from './components/AnalyticsView';
import PositionsView from './components/PositionsView';
import ReviewQueue from './components/ReviewQueue';
import { getReviewCount } from './services/api';
import type { InvestigationMessage, InvestigationThread } from './types';

type View = 'investigation' | 'analytics' | 'positions' | 'review';
const THREAD_STORAGE_KEY = 'ercot-copilot-threads';

function loadStoredThreads(): InvestigationThread[] {
  if (typeof window === 'undefined') return [];

  try {
    const raw = window.localStorage.getItem(THREAD_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((thread): thread is InvestigationThread =>
        typeof thread?.id === 'string' &&
        typeof thread?.title === 'string' &&
        Array.isArray(thread?.messages) &&
        typeof thread?.createdAt === 'number' &&
        typeof thread?.updatedAt === 'number'
      )
      .map(thread => ({
        ...thread,
        messages: thread.messages
          .filter((message): message is InvestigationMessage =>
            typeof message?.id === 'string' &&
            (message?.role === 'user' || message?.role === 'assistant') &&
            typeof message?.content === 'string'
          )
          .map(message =>
            message.streaming
              ? { ...message, streaming: false, content: message.content || '*(stopped)*' }
              : message
          ),
      }))
      .slice(0, 50);
  } catch {
    return [];
  }
}

export default function App() {
  const [activeView, setActiveView] = useState<View>('investigation');
  const [theme, setTheme] = useState<'copilot-dark' | 'copilot-light'>('copilot-dark');
  const [pendingReviews, setPendingReviews] = useState(0);
  const [threads, setThreads] = useState<InvestigationThread[]>(loadStoredThreads);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    window.localStorage.setItem(THREAD_STORAGE_KEY, JSON.stringify(threads.slice(0, 50)));
  }, [threads]);

  // Poll pending review count
  useEffect(() => {
    const fetchCount = async () => {
      try {
        const { pending } = await getReviewCount();
        setPendingReviews(pending);
      } catch {
        // backend not running — show 0
      }
    };
    fetchCount();
    const interval = setInterval(fetchCount, 60_000);
    return () => clearInterval(interval);
  }, []);

  const handlePendingCountChange = (count: number) => {
    setPendingReviews(count);
  };

  const toggleTheme = () =>
    setTheme(t => (t === 'copilot-dark' ? 'copilot-light' : 'copilot-dark'));

  const handleNewThread = () => {
    setActiveView('investigation');
    setActiveThreadId(null);
  };

  const handleThreadSelect = (threadId: string) => {
    setActiveView('investigation');
    setActiveThreadId(threadId);
  };

  const handleThreadDelete = (threadId: string) => {
    setThreads(prev => prev.filter(thread => thread.id !== threadId));
    if (activeThreadId === threadId) {
      setActiveView('investigation');
      setActiveThreadId(null);
    }
  };

  const views: Record<View, React.ReactNode> = {
    investigation: (
      <InvestigationView
        threads={threads}
        activeThreadId={activeThreadId}
        onThreadsChange={setThreads}
        onActiveThreadChange={setActiveThreadId}
      />
    ),
    analytics: <AnalyticsView />,
    positions: <PositionsView />,
    review: <ReviewQueue onPendingCountChange={handlePendingCountChange} />,
  };

  return (
    <div className="flex h-screen overflow-hidden bg-base-100">
      <Sidebar
        activeView={activeView}
        onViewChange={(v) => setActiveView(v as View)}
        darkMode={theme === 'copilot-dark'}
        onToggleDark={toggleTheme}
        pendingReviewCount={pendingReviews}
        chatThreads={threads}
        activeThreadId={activeThreadId}
        onNewThread={handleNewThread}
        onThreadSelect={handleThreadSelect}
        onThreadDelete={handleThreadDelete}
      />
      <main className="flex-1 overflow-hidden">
        {views[activeView]}
      </main>
    </div>
  );
}
