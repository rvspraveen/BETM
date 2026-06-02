/**
 * ERCOT Copilot — Centralized API Service
 *
 * All HTTP calls live here. Components never call fetch() directly.
 * Set VITE_MOCK_MODE=true in .env to use local mock data instead.
 */
import type { InvestigationVisualization } from '../types';

const BASE_URL = (import.meta as ImportMeta).env.VITE_API_URL || 'http://localhost:8000/api/v1';
const MOCK_MODE = (import.meta as ImportMeta).env.VITE_MOCK_MODE === 'true';

// ── SSE Investigation Stream ─────────────────────────────────────────────────

export interface SSEStatusEvent {
  type: 'status';
  step: string;
  content: string;
}

export interface SSETokenEvent {
  type: 'token';
  content: string;
}

export interface SSEMetadataEvent {
  type: 'metadata';
  investigation_id: string;
  sources: SourceRef[];
  confidence: number;
  escalated: boolean;
  intent: string;
  analytics_data?: Record<string, unknown>;
  visualizations?: InvestigationVisualization[];
  latency_ms?: number;
}

export interface SSEErrorEvent {
  type: 'error';
  content: string;
}

export interface SSEDoneEvent {
  type: 'done';
}

export type SSEEvent =
  | SSEStatusEvent
  | SSETokenEvent
  | SSEMetadataEvent
  | SSEErrorEvent
  | SSEDoneEvent;

export interface SourceRef {
  id: string;
  title: string;
  source_type: 'document' | 'market_data' | 'calculation';
  relevance_score: number;
  excerpt?: string;
  date?: string;
}

export interface InvestigateRequest {
  query: string;
  session_id?: string;
  filters?: Record<string, unknown>;
}

/**
 * Stream an investigation via SSE.
 * Calls onEvent for each event received.
 * Returns a cleanup function that aborts the stream.
 */
export function streamInvestigation(
  request: InvestigateRequest,
  onEvent: (event: SSEEvent) => void
): () => void {
  if (MOCK_MODE) {
    return _mockStreamInvestigation(request, onEvent);
  }

  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${BASE_URL}/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      if (!response.ok) {
        onEvent({ type: 'error', content: `API error: ${response.status} ${response.statusText}` });
        onEvent({ type: 'done' });
        return;
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.slice(6));
              onEvent(payload as SSEEvent);
            } catch {
              // skip malformed lines
            }
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name !== 'AbortError') {
        onEvent({ type: 'error', content: String(err) });
        onEvent({ type: 'done' });
      }
    }
  })();

  return () => controller.abort();
}

// ── Documents ────────────────────────────────────────────────────────────────

export interface DocumentOut {
  id: number;
  title: string;
  doc_type: string;
  source: string;
  effective_date?: string;
  ingested_at: string;
  chunk_count: number;
}

export async function getDocuments(): Promise<DocumentOut[]> {
  if (MOCK_MODE) return _mock('documents') as Promise<DocumentOut[]>;
  const r = await fetch(`${BASE_URL}/documents`);
  return r.json();
}

// ── Datasets ─────────────────────────────────────────────────────────────────

export interface DatasetSummary {
  name: string;
  table: string;
  row_count: number;
  description: string;
}

export async function getDatasets(): Promise<DatasetSummary[]> {
  if (MOCK_MODE) return _mock('datasets') as Promise<DatasetSummary[]>;
  const r = await fetch(`${BASE_URL}/datasets`);
  return r.json();
}

// ── Analytics ────────────────────────────────────────────────────────────────

export async function getPriceSpikes(threshold = 200, hoursBack = 168, market = 'rt') {
  if (MOCK_MODE) return _mock('price_spikes');
  const r = await fetch(`${BASE_URL}/analytics/price-spikes?threshold=${threshold}&hours_back=${hoursBack}&market=${market}`);
  return r.json();
}

export async function getDaRtDivergence(nodeId?: string, hoursBack = 48) {
  if (MOCK_MODE) return _mock('da_rt_divergence');
  const params = new URLSearchParams({ hours_back: String(hoursBack) });
  if (nodeId) params.set('node_id', nodeId);
  const r = await fetch(`${BASE_URL}/analytics/da-rt-divergence?${params}`);
  return r.json();
}

export async function getPositions(book?: string) {
  if (MOCK_MODE) return _mock('positions');
  const params = book ? `?book=${encodeURIComponent(book)}` : '';
  const r = await fetch(`${BASE_URL}/analytics/positions${params}`);
  return r.json();
}

export async function getPnlSummary(daysBack = 30, book?: string) {
  if (MOCK_MODE) return _mock('pnl');
  const params = new URLSearchParams({ days_back: String(daysBack) });
  if (book) params.set('book', book);
  const r = await fetch(`${BASE_URL}/analytics/pnl-summary?${params}`);
  return r.json();
}

export async function getGenerationMix(hoursBack = 24) {
  if (MOCK_MODE) return _mock('generation_mix');
  const r = await fetch(`${BASE_URL}/analytics/generation-mix?hours_back=${hoursBack}`);
  return r.json();
}

// ── Review Queue ─────────────────────────────────────────────────────────────

export interface ReviewItem {
  id: number;
  investigation_id: string;
  query_text: string;
  ai_answer: string;
  confidence: number;
  escalation_reason: string;
  status: 'pending' | 'approved' | 'rejected';
  reviewer_notes?: string;
  created_at: string;
  resolved_at?: string;
}

export async function getReviews(status = 'pending'): Promise<ReviewItem[]> {
  if (MOCK_MODE) return _mock('reviews') as Promise<ReviewItem[]>;
  const r = await fetch(`${BASE_URL}/reviews?status=${status}`);
  return r.json();
}

export async function getReviewCount(): Promise<{ pending: number }> {
  if (MOCK_MODE) return { pending: 3 };
  const r = await fetch(`${BASE_URL}/reviews/count`);
  return r.json();
}

export async function resolveReview(
  id: number,
  status: 'approved' | 'rejected',
  notes?: string
): Promise<ReviewItem> {
  if (MOCK_MODE) return { id, status } as ReviewItem;
  const r = await fetch(`${BASE_URL}/reviews/${id}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, reviewer_notes: notes }),
  });
  return r.json();
}

// ── Health ───────────────────────────────────────────────────────────────────

export interface HealthStatus {
  status: 'ok' | 'degraded';
  version: string;
  llm_provider: string;
  llm_model: string;
  database: string;
}

export async function getHealth(): Promise<HealthStatus> {
  const r = await fetch(`${BASE_URL.replace('/api/v1', '')}/api/v1/health`);
  return r.json();
}

export async function getExamples() {
  if (MOCK_MODE) return [];
  const r = await fetch(`${BASE_URL}/examples`);
  return r.json();
}

// ── Mock fallbacks (VITE_MOCK_MODE=true) ────────────────────────────────────

function _mock(key: string): Promise<unknown[]> {
  return import('../data/mockData').then((m) => {
    const map: Record<string, unknown[]> = {
      documents: [],
      datasets: [],
      price_spikes: [],
      da_rt_divergence: [],
      positions: (m.MOCK_POSITIONS as unknown[]) ?? [],
      pnl: [],
      generation_mix: [],
      reviews: (m.MOCK_REVIEW_ITEMS as unknown[]) ?? [],
    };
    return map[key] ?? [];
  });
}

function _mockStreamInvestigation(
  request: InvestigateRequest,
  onEvent: (event: SSEEvent) => void
): () => void {
  let cancelled = false;
  const steps: SSEEvent[] = [
    { type: 'status', step: 'classifier', content: '🔍 Classifying your query…' },
    { type: 'status', step: 'classifier', content: '📋 Intent: **hybrid** — Requires both document retrieval and quantitative analysis.' },
    { type: 'status', step: 'entity_extractor', content: '🏷️ Extracting entities…' },
    { type: 'status', step: 'entity_extractor', content: '🏷️ Found nodes: HB_HOUSTON; dates: 2024-06-15' },
    { type: 'status', step: 'retriever', content: '📚 Searching 847 indexed document chunks…' },
    { type: 'status', step: 'retriever', content: '📄 Found 4 relevant chunks — top: "ERCOT Market Notice MN-2024-0892" (91% match)' },
    { type: 'status', step: 'analytics', content: '📊 Running quantitative analysis…' },
    { type: 'status', step: 'analytics', content: '📊 Computed: price_spikes, da_rt_divergence, congestion_exposure' },
    { type: 'status', step: 'synthesizer', content: '✍️ Synthesizing answer with LLM…' },
  ];

  const answerTokens = `## Price Spike Analysis — HB_HOUSTON June 15, 2024

**Summary:** Real-time prices at HB_HOUSTON reached **$850/MWh** between 14:00–16:00 CDT on June 15, 2024 — roughly 20× the typical summer average of $43/MWh.

### Root Causes (Dual Event)

1. **Forced Outage — Brazos Valley Unit 3** *(MN-2024-0892)*
   - 750 MW removed from service at 13:22 CDT (high exhaust temp alarm)
   - Reduced Houston load pocket supply by ~27%

2. **Transmission Constraint — Sabine-Jasper 345kV** *(MN-2024-1021)*
   - Emergency outage 22:00 June 14 through 20:00 June 15
   - Import capability from East Texas cut by ~40%
   - SABINE_345 shadow price peaked at **$310/MWh**

### Market Data
| Metric | Value |
|---|---|
| RT Price Peak (HB_HOUSTON) | $850/MWh |
| DA Price (same interval) | $420/MWh |
| DA/RT Divergence | +$430/MWh |
| SABINE_345 Shadow Price | $310/MWh |
| Net Congestion Rent | $245,000 |

### Trading Implications
- Long RT positions at HB_HOUSTON captured +$430/MWh premium over DA
- CRR holders on BUS_BRAZOS → HB_HOUSTON path received full congestion credit
- ERCOT_SOUTH and ERCOT_HUB books showed P&L of ~$180K on this event

**Confidence: High** — dual corroborating sources (market notices + RT price data)`.split(' ');

  const runSequence = async () => {
    // Play status steps
    for (let i = 0; i < steps.length; i++) {
      if (cancelled) return;
      await new Promise(r => setTimeout(r, 300 + Math.random() * 400));
      onEvent(steps[i]);
    }
    // Stream answer tokens
    for (const token of answerTokens) {
      if (cancelled) return;
      await new Promise(r => setTimeout(r, 25 + Math.random() * 30));
      onEvent({ type: 'token', content: token + ' ' });
    }
    if (!cancelled) {
      onEvent({
        type: 'metadata',
        investigation_id: 'mock-inv-001',
        sources: [
          { id: '1', title: 'ERCOT Market Notice MN-2024-0892', source_type: 'document', relevance_score: 0.91, date: '2024-06-15' },
          { id: '2', title: 'ERCOT Market Notice MN-2024-1021', source_type: 'document', relevance_score: 0.88, date: '2024-06-14' },
          { id: '3', title: 'RT Price Data — HB_HOUSTON', source_type: 'market_data', relevance_score: 1.0, date: '2024-06-15' },
        ],
        confidence: 0.91,
        escalated: false,
        intent: 'hybrid',
        visualizations: [
          {
            id: 'mock_price_spike_summary',
            type: 'kpi',
            title: 'Price Spike Summary',
            description: 'Structured payload rendered from investigation metadata.',
            metrics: [
              { label: 'RT Peak', value: '$850.00', detail: 'HB_HOUSTON', tone: 'error' },
              { label: 'DA/RT Spread', value: '$430.00', tone: 'warning' },
              { label: 'Shadow Price', value: '$310.00', detail: 'SABINE_345', tone: 'warning' },
            ],
          },
          {
            id: 'mock_da_rt_chart',
            type: 'bar',
            title: 'DA vs RT Price',
            description: 'Example chart generated from metadata JSON.',
            data: [
              { hour: 'HE13', da_lmp: 82, rt_lmp: 145 },
              { hour: 'HE14', da_lmp: 420, rt_lmp: 850 },
              { hour: 'HE15', da_lmp: 390, rt_lmp: 790 },
              { hour: 'HE16', da_lmp: 110, rt_lmp: 245 },
            ],
            xKey: 'hour',
            unit: '$/MWh',
            yKeys: [
              { key: 'da_lmp', label: 'DA', color: '#60a5fa' },
              { key: 'rt_lmp', label: 'RT', color: '#a78bfa' },
            ],
          },
        ],
        latency_ms: 2840,
      });
      onEvent({ type: 'done' });
    }
  };

  runSequence();
  return () => { cancelled = true; };
}
