/**
 * Human Review Queue — items escalated from the AI workflow.
 * Calls GET /api/v1/reviews and POST /api/v1/reviews/{id}/resolve.
 */
import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, ChevronDown, ChevronRight, AlertTriangle, RefreshCw } from 'lucide-react';
import { getReviews, resolveReview, ReviewItem } from '../services/api';

interface Props {
  onPendingCountChange: (count: number) => void;
}

export default function ReviewQueue({ onPendingCountChange }: Props) {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'pending' | 'approved' | 'rejected' | 'all'>('pending');
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getReviews(filter);
      setItems(data);
      const pendingCount = filter === 'pending' ? data.length : data.filter(i => i.status === 'pending').length;
      onPendingCountChange(pendingCount);
    } catch (e) {
      console.error('Failed to load reviews', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filter]);

  const handleResolve = async (id: number, status: 'approved' | 'rejected') => {
    setResolvingId(id);
    try {
      await resolveReview(id, status);
      setItems(prev => prev.map(i => i.id === id ? { ...i, status } : i));
      // Refresh pending count
      const pending = items.filter(i => i.id !== id && i.status === 'pending').length;
      onPendingCountChange(pending);
    } catch (e) {
      console.error('Failed to resolve review', e);
    } finally {
      setResolvingId(null);
    }
  };

  const confidenceColor = (c: number) =>
    c >= 0.8 ? 'text-success' : c >= 0.65 ? 'text-warning' : 'text-error';

  const statusBadge = (s: string) => {
    const map: Record<string, string> = {
      pending: 'badge-warning',
      approved: 'badge-success',
      rejected: 'badge-error',
    };
    return `badge badge-sm ${map[s] ?? 'badge-ghost'}`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-base-300 flex items-center gap-3">
        <AlertTriangle size={18} className="text-warning" />
        <h1 className="text-lg font-semibold">Review Queue</h1>
        <div className="ml-auto flex items-center gap-2">
          {/* Filter tabs */}
          <div className="tabs tabs-boxed tabs-sm">
            {(['pending', 'approved', 'rejected', 'all'] as const).map(f => (
              <button
                key={f}
                className={`tab tab-sm capitalize ${filter === f ? 'tab-active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
          <button className="btn btn-ghost btn-xs" onClick={load} title="Refresh">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center h-32 opacity-50">
            <RefreshCw size={20} className="animate-spin mr-2" /> Loading…
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 opacity-40 gap-3">
            <CheckCircle size={40} />
            <p>No {filter === 'all' ? '' : filter} items</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map(item => (
              <div key={item.id} className="card bg-base-200 shadow-sm">
                <div className="card-body p-4">
                  {/* Header row */}
                  <div className="flex items-start gap-2">
                    <button
                      className="mt-0.5 text-base-content/50 hover:text-base-content"
                      onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                    >
                      {expanded === item.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </button>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className={statusBadge(item.status)}>{item.status}</span>
                        <span className={`text-xs font-semibold ${confidenceColor(item.confidence)}`}>
                          {(item.confidence * 100).toFixed(0)}% confidence
                        </span>
                        <span className="text-xs opacity-40">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm font-medium truncate">{item.query_text}</p>
                      <p className="text-xs opacity-50 mt-0.5 truncate">{item.escalation_reason}</p>
                    </div>

                    {/* Action buttons — only for pending */}
                    {item.status === 'pending' && (
                      <div className="flex gap-2 shrink-0">
                        <button
                          className="btn btn-sm btn-success gap-1"
                          disabled={resolvingId === item.id}
                          onClick={() => handleResolve(item.id, 'approved')}
                        >
                          <CheckCircle size={14} />
                          Approve
                        </button>
                        <button
                          className="btn btn-sm btn-error gap-1"
                          disabled={resolvingId === item.id}
                          onClick={() => handleResolve(item.id, 'rejected')}
                        >
                          <XCircle size={14} />
                          Reject
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Expanded answer */}
                  {expanded === item.id && (
                    <div className="mt-3 pt-3 border-t border-base-300 ml-6">
                      <p className="text-xs font-semibold opacity-60 mb-2">AI Answer</p>
                      <div className="text-sm bg-base-100 rounded-lg p-3 max-h-64 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                        {item.ai_answer}
                      </div>
                      {item.reviewer_notes && (
                        <div className="mt-2">
                          <p className="text-xs font-semibold opacity-60 mb-1">Reviewer Notes</p>
                          <p className="text-sm opacity-70">{item.reviewer_notes}</p>
                        </div>
                      )}
                      <p className="text-xs opacity-40 mt-2">ID: {item.investigation_id}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
