// =============================================================================
// ERCOT Copilot — Mock Data
// TODO: Replace each exported constant with an API call to the backend.
// =============================================================================

import type {
  ChatMessage, MetricCard, HourlyPrice, NodePrice,
  CongestionEvent, Position, ReviewItem, QueryCapabilityGroup,
} from '../types';

// ── Review Queue ──────────────────────────────────────────────────────────
export const MOCK_REVIEW_ITEMS: ReviewItem[] = [
  {
    id: 'r1',
    title: 'Unusual DA/RT Spread — HB_NORTH, 2025-03-15 HE14',
    summary: 'Detected $287/MWh spread between DA and RT prices at HB_NORTH during peak hour HE14.',
    detail: 'The LMP spike was driven by binding constraint CORYCELL_138KV combined with high wind curtailment in West zone. Settlement implication: ~$420K exposure for Book North. Recommend review before auto-approval.',
    confidence: 0.91,
    category: 'Price Anomaly',
    status: 'pending',
    createdAt: '2025-03-15T15:30:00Z',
  },
  {
    id: 'r2',
    title: 'Settlement Variance > $50K — Book Houston, March 14',
    summary: 'Total settlement variance of $73,400 identified for Book Houston across 6 nodes.',
    detail: 'Primary driver is Node WOODLANDS_69KV with $41,200 variance attributed to unscheduled outage OTG-2025-0312. Documentation cross-reference found matching ERCOT Notice #4821 but timing mismatch of 23 minutes requires manual verification.',
    confidence: 0.78,
    category: 'Settlement',
    status: 'pending',
    createdAt: '2025-03-14T22:10:00Z',
  },
  {
    id: 'r3',
    title: 'Congestion Pattern — CORYCELL Constraint Repeat',
    summary: 'CORYCELL_138KV constraint has bound in 14 of last 21 days, indicating structural issue.',
    detail: 'Pattern analysis suggests this is not transient — likely requires transmission planning review. Shadow price averaging $145/MWh during binding periods. Associated documentation references ERCOT Nodal Protocol §6.5.7.',
    confidence: 0.96,
    category: 'Congestion',
    status: 'approved',
    createdAt: '2025-03-13T09:00:00Z',
    reviewer: 'J. Martinez',
  },
  {
    id: 'r4',
    title: 'Alias Conflict — Node HOUSTON_SAN_JACINTO',
    summary: 'Node appears under 3 different aliases across settlement, forecast and outage datasets.',
    detail: 'Aliases detected: HOUSTON_SAN_JACINTO, HSJ_69KV, and HSJ_BUS. Cross-dataset joins may produce incorrect aggregations. Recommend alias table update before next settlement run.',
    confidence: 0.85,
    category: 'Data Quality',
    status: 'rejected',
    createdAt: '2025-03-12T14:20:00Z',
    reviewer: 'A. Chen',
  },
];

// ── Metric Cards ──────────────────────────────────────────────────────────
// TODO: replace with GET /api/analytics/metrics?date=...
export const MOCK_METRICS: MetricCard[] = [
  { label: 'Avg DA Price',      value: '$52.40/MWh',  delta: '+$4.20',   trend: 'up',   positive: false },
  { label: 'DA/RT Spread',      value: '$8.73/MWh',   delta: '+$2.10',   trend: 'up',   positive: false },
  { label: 'Peak LMP Spike',    value: '$287/MWh',    delta: 'HB_NORTH', trend: 'up',   positive: false },
  { label: 'Settlement Var.',   value: '$127K',        delta: '3 books',  trend: 'down', positive: true  },
];

// ── Hourly Prices ─────────────────────────────────────────────────────────
// TODO: replace with GET /api/analytics/prices?date=...&node=HB_NORTH
export const MOCK_HOURLY_PRICES: HourlyPrice[] = Array.from({ length: 24 }, (_, i) => ({
  hour: i + 1,
  da: 30 + Math.sin(i / 3) * 15 + (i >= 7 && i <= 19 ? 15 : 0) + (i === 14 ? 210 : 0),
  rt: 28 + Math.sin(i / 3) * 18 + (i >= 7 && i <= 19 ? 12 : 0) + (i === 14 ? 235 : 0),
}));

// ── Node Prices ───────────────────────────────────────────────────────────
// TODO: replace with GET /api/analytics/nodes?date=...
export const MOCK_NODE_PRICES: NodePrice[] = [
  { node: 'HB_NORTH',       da: 54.2,  rt: 287.4, spread: 233.2, congested: true  },
  { node: 'HB_WEST',        da: 49.1,  rt:  61.3, spread:  12.2, congested: false },
  { node: 'HB_HOUSTON',     da: 55.8,  rt:  62.4, spread:   6.6, congested: false },
  { node: 'HB_SOUTH',       da: 52.3,  rt:  58.9, spread:   6.6, congested: false },
  { node: 'CORYCELL_138',   da: 38.7,  rt: 189.2, spread: 150.5, congested: true  },
  { node: 'WOODLANDS_69',   da: 56.1,  rt:  71.4, spread:  15.3, congested: false },
  { node: 'ABILENE_138',    da: 44.2,  rt:  48.9, spread:   4.7, congested: false },
  { node: 'LAREDO_345',     da: 51.4,  rt:  53.1, spread:   1.7, congested: false },
];

// ── Congestion ────────────────────────────────────────────────────────────
// TODO: replace with GET /api/analytics/congestion?date=...
export const MOCK_CONGESTION: CongestionEvent[] = [
  { constraint: 'CORYCELL_138KV',  from: 'HB_WEST',    to: 'HB_NORTH',   shadow: 198.7, severity: 'high',   pctOfLimit: 94 },
  { constraint: 'LAMAR_345KV',     from: 'HB_NORTH',   to: 'HB_HOUSTON', shadow:  74.2, severity: 'medium', pctOfLimit: 67 },
  { constraint: 'BRYAN_138KV',     from: 'HB_SOUTH',   to: 'HB_HOUSTON', shadow:  31.5, severity: 'low',    pctOfLimit: 38 },
  { constraint: 'SANDOW_345KV',    from: 'HB_WEST',    to: 'HB_SOUTH',   shadow:  22.1, severity: 'low',    pctOfLimit: 29 },
];

// ── Positions ─────────────────────────────────────────────────────────────
// TODO: replace with GET /api/positions?book=...
export const MOCK_POSITIONS: Position[] = [
  { id: 'p1',  book: 'North',   node: 'HB_NORTH',     direction: 'Long',  volumeMwh: 450,  daPrice: 54.2,  rtPrice: 287.4, pnlUsd:  104895, status: 'open'     },
  { id: 'p2',  book: 'North',   node: 'CORYCELL_138', direction: 'Short', volumeMwh: 200,  daPrice: 38.7,  rtPrice: 189.2, pnlUsd: -30100,  status: 'open'     },
  { id: 'p3',  book: 'West',    node: 'HB_WEST',      direction: 'Long',  volumeMwh: 300,  daPrice: 49.1,  rtPrice:  61.3, pnlUsd:   3660,  status: 'open'     },
  { id: 'p4',  book: 'West',    node: 'ABILENE_138',  direction: 'Short', volumeMwh: 150,  daPrice: 44.2,  rtPrice:  48.9, pnlUsd:    -705, status: 'open'     },
  { id: 'p5',  book: 'South',   node: 'HB_SOUTH',     direction: 'Long',  volumeMwh: 500,  daPrice: 52.3,  rtPrice:  58.9, pnlUsd:   3300,  status: 'settled'  },
  { id: 'p6',  book: 'South',   node: 'LAREDO_345',   direction: 'Short', volumeMwh: 220,  daPrice: 51.4,  rtPrice:  53.1, pnlUsd:    -374, status: 'settled'  },
  { id: 'p7',  book: 'Houston', node: 'HB_HOUSTON',   direction: 'Long',  volumeMwh: 380,  daPrice: 55.8,  rtPrice:  62.4, pnlUsd:   2508,  status: 'open'     },
  { id: 'p8',  book: 'Houston', node: 'WOODLANDS_69', direction: 'Short', volumeMwh: 175,  daPrice: 56.1,  rtPrice:  71.4, pnlUsd:  -2678,  status: 'open'     },
];

// ── Query Capability Groups ───────────────────────────────────────────────
export const QUERY_CAPABILITY_GROUPS: QueryCapabilityGroup[] = [
  {
    id: 'market',
    label: 'Market Behavior',
    tagline: 'Price formation, congestion events and operational drivers',
    color: 'text-blue-400',
    border: 'border-blue-500/40',
    bg: 'bg-blue-500/10',
    chipClass: 'chip-doc',
    queries: [
      { text: 'What likely drove the congestion spike on a given date/hour?', kind: 'hybrid_query' },
      { text: 'Why did real-time prices diverge from day-ahead prices at a node or hub?', kind: 'analytics_query' },
      { text: 'Which outages or constraints coincided with a price event?', kind: 'hybrid_query' },
    ],
  },
  {
    id: 'exposure',
    label: 'Exposure & Risk',
    tagline: 'Portfolio exposure, volatility and historical similarity',
    color: 'text-emerald-400',
    border: 'border-emerald-500/40',
    bg: 'bg-emerald-500/10',
    chipClass: 'chip-analyt',
    queries: [
      { text: 'Which positions were most exposed to congestion in a selected period?', kind: 'analytics_query' },
      { text: 'What historical events most resemble the selected basis pattern?', kind: 'hybrid_query' },
      { text: 'Which assets or books showed the largest volatility-adjusted exposure?', kind: 'analytics_query' },
    ],
  },
  {
    id: 'rules',
    label: 'Rules & Market Context',
    tagline: 'ISO rules, notices, manuals and settlement context',
    color: 'text-amber-400',
    border: 'border-amber-500/40',
    bg: 'bg-amber-500/10',
    chipClass: 'chip-uncert',
    queries: [
      { text: 'Which ISO rules or market notices are relevant to this event?', kind: 'doc_query' },
      { text: 'Did any recent manual changes affect settlement or auction logic?', kind: 'doc_query' },
      { text: 'Which documents describe congestion management or uplift treatment?', kind: 'doc_query' },
    ],
  },
  {
    id: 'hybrid',
    label: 'Hybrid Analysis',
    tagline: 'Fuses structured data with document context for root-cause analysis',
    color: 'text-violet-400',
    border: 'border-violet-500/40',
    bg: 'bg-violet-500/10',
    chipClass: 'chip-hybrid',
    queries: [
      { text: 'Compare historical price spikes with known outage notices and explain likely drivers.', kind: 'hybrid_query' },
      { text: 'Summarize portfolio exposure for a trading book and cite relevant market conditions and operational notices.', kind: 'hybrid_query' },
      { text: 'Explain a settlement variance using both structured settlement data and supporting documents.', kind: 'hybrid_query' },
    ],
  },
];

// ── Initial chat messages ─────────────────────────────────────────────────
export const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-0',
    role: 'assistant',
    kind: 'plain',
    text: 'Good morning. I\'m your ERCOT power market intelligence copilot. I can investigate price anomalies, analyze congestion patterns, reconcile settlement variances, and answer questions grounded in ERCOT protocols and your live market data.\n\nSelect a query below or type your own.',
    timestamp: new Date(Date.now() - 120_000),
  },
];
