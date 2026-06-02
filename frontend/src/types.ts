// ── View routing ───────────────────────────────────────────────────────────
export type ViewType = 'investigation' | 'analytics' | 'positions' | 'review';

// ── Chat ───────────────────────────────────────────────────────────────────
export type MessageRole = 'user' | 'assistant' | 'thinking';

export interface ReasoningStep {
  label: string;
  detail: string;
  durationMs: number;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  text?: string;
  /** Typed response kind for rich rendering */
  kind?: 'price_spike' | 'settlement_variance' | 'doc_query' | 'analytics_query' | 'hybrid_query' | 'uncertainty_query' | 'plain';
  timestamp: Date;
  reasoning?: ReasoningStep[];
}

export interface InvestigationReasoningStep {
  step: string;
  content: string;
  done: boolean;
}

export interface InvestigationSourceRef {
  id: string;
  title: string;
  source_type: 'document' | 'market_data' | 'calculation';
  relevance_score: number;
  excerpt?: string;
  date?: string;
}

export type VisualizationType = 'kpi' | 'bar' | 'line' | 'pie' | 'table';

export interface VisualizationSeries {
  key: string;
  label: string;
  color?: string;
}

export interface VisualizationColumn {
  key: string;
  label: string;
}

export interface VisualizationMetric {
  label: string;
  value: string;
  detail?: string;
  tone?: 'neutral' | 'success' | 'warning' | 'error';
}

export interface InvestigationVisualization {
  id: string;
  type: VisualizationType;
  title: string;
  description?: string;
  data?: Record<string, unknown>[];
  xKey?: string;
  unit?: string;
  yKeys?: VisualizationSeries[];
  columns?: VisualizationColumn[];
  metrics?: VisualizationMetric[];
}

export interface InvestigationMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  reasoning?: InvestigationReasoningStep[];
  sources?: InvestigationSourceRef[];
  visualizations?: InvestigationVisualization[];
  confidence?: number;
  escalated?: boolean;
  intent?: string;
  latency_ms?: number;
  streaming?: boolean;
  error?: boolean;
}

export interface InvestigationThread {
  id: string;
  title: string;
  messages: InvestigationMessage[];
  createdAt: number;
  updatedAt: number;
}

// ── Analytics ──────────────────────────────────────────────────────────────
export interface MetricCard {
  label: string;
  value: string;
  delta: string;
  trend: 'up' | 'down' | 'flat';
  positive: boolean; // whether upward trend is good
}

export interface HourlyPrice {
  hour: number;
  da: number;
  rt: number;
}

export interface NodePrice {
  node: string;
  da: number;
  rt: number;
  spread: number;
  congested: boolean;
}

export interface CongestionEvent {
  constraint: string;
  from: string;
  to: string;
  shadow: number;
  severity: 'high' | 'medium' | 'low';
  pctOfLimit: number;
}

// ── Positions ──────────────────────────────────────────────────────────────
export type Book = 'All' | 'North' | 'West' | 'South' | 'Houston';

export interface Position {
  id: string;
  book: Exclude<Book, 'All'>;
  node: string;
  direction: 'Long' | 'Short';
  volumeMwh: number;
  daPrice: number;
  rtPrice: number;
  pnlUsd: number;
  status: 'open' | 'settled';
}

// ── Review Queue ───────────────────────────────────────────────────────────
export type ReviewStatus = 'pending' | 'approved' | 'rejected';

export interface ReviewItem {
  id: string;
  title: string;
  summary: string;
  detail: string;
  confidence: number;
  category: string;
  status: ReviewStatus;
  createdAt: string;
  reviewer?: string;
}

// ── Query Capabilities ─────────────────────────────────────────────────────
export type QueryCategory = 'market' | 'exposure' | 'rules' | 'hybrid';

export interface QueryChip {
  text: string;
  /** Which kind of mock response to show when auto-sent */
  kind: ChatMessage['kind'];
}

export interface QueryCapabilityGroup {
  id: QueryCategory;
  label: string;
  tagline: string;
  color: string;           // tailwind text color class
  border: string;          // tailwind border color class
  bg: string;              // tailwind bg class (active tab)
  chipClass: string;       // extra class on chips
  queries: QueryChip[];
}
