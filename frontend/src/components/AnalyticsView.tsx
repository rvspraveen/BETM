/**
 * Analytics Dashboard — date picker, KPI cards, DA/RT chart, heatmap, congestion table.
 * TODO: Replace MOCK_* constants with GET /api/analytics/... calls.
 */
import React, { useState } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, Minus, Calendar } from 'lucide-react';
import { MOCK_METRICS, MOCK_HOURLY_PRICES, MOCK_NODE_PRICES, MOCK_CONGESTION } from '../data/mockData';
import { DashboardContextPanel, ContextSection } from './DashboardContextPanel';

type AnalyticsContextId = 'overview' | 'controls' | 'kpis' | 'price_chart' | 'node_heatmap' | 'constraints';

const ANALYTICS_CONTEXT: ContextSection[] = [
  {
    id: 'overview',
    title: 'Market Data Dashboard',
    summary: 'Deterministic view of prices, congestion, and grid conditions.',
    datasets: ['da_lmp.csv', 'rt_lmp.csv', 'constraints.csv'],
    signals: [
      'Use this first to spot anomalies before checking exposure or asking Investigate.',
    ],
  },
  {
    id: 'controls',
    title: 'Date and Refresh Controls',
    summary: 'Sets the operating day or analysis window.',
    datasets: ['da_lmp.csv', 'rt_lmp.csv', 'constraints.csv'],
    signals: [
      'Changing this updates the price, constraint, outage, and load window.',
    ],
  },
  {
    id: 'kpis',
    title: 'Market KPI Cards',
    summary: 'Quick read on price level, spread, settlement impact, and movement.',
    datasets: ['da_lmp.csv', 'rt_lmp.csv', 'settlements.csv'],
    signals: [
      'Large deltas mark where to drill into hourly or node-level detail.',
    ],
  },
  {
    id: 'price_chart',
    title: 'DA vs RT Price Chart',
    summary: 'Hourly DA vs RT comparison for divergence and spikes.',
    datasets: ['da_lmp.csv', 'rt_lmp.csv'],
    signals: [
      'Wide RT-DA gaps often point to outages, constraints, or scarcity.',
    ],
  },
  {
    id: 'node_heatmap',
    title: 'Node Price Heatmap',
    summary: 'Ranks nodes by spread to show where the event localized.',
    datasets: ['da_lmp.csv', 'rt_lmp.csv', 'asset_metadata.csv'],
    signals: [
      'High spread rows are the fastest path to basis-risk hot spots.',
    ],
  },
  {
    id: 'constraints',
    title: 'Active Congestion Constraints',
    summary: 'Binding constraints and shadow prices behind LMP separation.',
    datasets: ['constraints.csv', 'outages.csv', 'congestion_archive.csv'],
    signals: [
      'Higher shadow price and loading means stronger congestion pressure.',
    ],
  },
];

// ── Metric card ────────────────────────────────────────────────────────────
const MetricCard: React.FC<{
  label: string; value: string; delta: string; trend: 'up'|'down'|'flat'; positive: boolean;
  contextProps?: React.HTMLAttributes<HTMLDivElement>;
}> = ({ label, value, delta, trend, positive, contextProps }) => {
  const good = (trend === 'up' && positive) || (trend === 'down' && !positive);
  const color = trend === 'flat' ? 'text-base-content/50'
              : good ? 'text-success' : 'text-error';
  const Icon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  return (
    <div {...contextProps} className="card bg-base-200 border border-base-content/10 p-4 flex-1 min-w-[140px]">
      <p className="text-[10px] uppercase tracking-widest text-base-content/40 font-semibold mb-1">{label}</p>
      <p className="text-xl font-bold text-base-content mb-1">{value}</p>
      <div className={`flex items-center gap-1 text-xs font-medium ${color}`}>
        <Icon size={12} />
        <span>{delta}</span>
      </div>
    </div>
  );
};

// ── DA/RT Bar Chart ────────────────────────────────────────────────────────
const PriceChart: React.FC<{ contextProps?: React.HTMLAttributes<HTMLDivElement> }> = ({ contextProps }) => {
  const data = MOCK_HOURLY_PRICES;
  // Cap spike for display
  const capped = data.map(d => ({ ...d, da: Math.min(d.da, 120), rt: Math.min(d.rt, 120) }));
  const maxVal = Math.max(...capped.flatMap(d => [d.da, d.rt]));
  const CHART_H = 120;

  return (
    <div {...contextProps} className="card bg-base-200 border border-base-content/10 p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-bold text-base-content">DA vs RT Price ($/MWh) — 24h</p>
        <div className="flex gap-3">
          {[['DA', 'bg-primary/60'], ['RT', 'bg-secondary/60']].map(([l, c]) => (
            <span key={l} className="flex items-center gap-1 text-[10px] text-base-content/50">
              <span className={`w-2 h-2 rounded-sm ${c} inline-block`} /> {l}
            </span>
          ))}
        </div>
      </div>
      <div className="flex items-end gap-0.5 overflow-x-auto pb-2" style={{ height: CHART_H + 24 }}>
        {capped.map((d, i) => (
          <div key={i} className="flex flex-col items-center gap-0.5 flex-1 min-w-[14px]">
            <div className="flex gap-0.5 items-end" style={{ height: CHART_H }}>
              <div
                className={`flex-1 rounded-t transition-all ${
                  data[i].rt > 200 ? 'bg-error/70' : 'bg-primary/60'
                }`}
                style={{ height: `${(d.da / maxVal) * 100}%` }}
                title={`HE${d.hour} DA: $${data[i].da.toFixed(0)}`}
              />
              <div
                className={`flex-1 rounded-t transition-all ${
                  data[i].rt > 200 ? 'bg-error' : 'bg-secondary/60'
                }`}
                style={{ height: `${(d.rt / maxVal) * 100}%` }}
                title={`HE${d.hour} RT: $${data[i].rt.toFixed(0)}`}
              />
            </div>
            {i % 3 === 0 && (
              <span className="text-[8px] text-base-content/30">{d.hour}</span>
            )}
          </div>
        ))}
      </div>
      <p className="text-[10px] text-base-content/25 text-right">HE14 spike capped at $120 for display clarity</p>
    </div>
  );
};

// ── Node Heatmap ───────────────────────────────────────────────────────────
const NodeHeatmap: React.FC<{ contextProps?: React.HTMLAttributes<HTMLDivElement> }> = ({ contextProps }) => {
  const spreadColorClass = (spread: number) => {
    if (spread > 100) return 'bg-error/80 text-error-content font-bold';
    if (spread > 20)  return 'bg-warning/60 text-base-content font-semibold';
    if (spread > 8)   return 'bg-warning/25 text-base-content';
    return 'bg-base-300/40 text-base-content/60';
  };

  return (
    <div {...contextProps} className="card bg-base-200 border border-base-content/10 p-4">
      <p className="text-xs font-bold text-base-content mb-3">Node Price Heatmap — Spread ($/MWh)</p>
      <div className="overflow-x-auto">
        <table className="table table-xs w-full">
          <thead>
            <tr className="bg-base-300/60">
              {['Node', 'DA', 'RT', 'Spread', 'Status'].map(h => (
                <th key={h} className="text-[10px] uppercase tracking-wider text-base-content/40">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {MOCK_NODE_PRICES.map(row => (
              <tr key={row.node} className="border-base-content/5 hover:bg-base-300/20">
                <td className="font-mono text-xs text-base-content">{row.node}</td>
                <td className="text-xs">${row.da.toFixed(1)}</td>
                <td className={`text-xs font-semibold ${row.rt > 100 ? 'text-error' : ''}`}>
                  ${row.rt.toFixed(1)}
                </td>
                <td className={`text-xs px-2 py-1`}>
                  <span className={`px-2 py-0.5 rounded text-xs ${spreadColorClass(row.spread)}`}>
                    ${row.spread.toFixed(1)}
                  </span>
                </td>
                <td>
                  {row.congested
                    ? <span className="badge badge-xs badge-error gap-1">Congested</span>
                    : <span className="badge badge-xs badge-ghost opacity-50">Normal</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ── Congestion Table ───────────────────────────────────────────────────────
const CongestionTable: React.FC<{ contextProps?: React.HTMLAttributes<HTMLDivElement> }> = ({ contextProps }) => (
  <div {...contextProps} className="card bg-base-200 border border-base-content/10 p-4">
    <p className="text-xs font-bold text-base-content mb-3">Active Congestion Constraints</p>
    <div className="space-y-3">
      {MOCK_CONGESTION.map(c => (
        <div key={c.constraint} className="rounded-lg bg-base-300/40 p-3">
          <div className="flex items-start justify-between mb-2">
            <div>
              <p className="text-xs font-semibold text-base-content">{c.constraint}</p>
              <p className="text-[10px] text-base-content/40">{c.from} → {c.to}</p>
            </div>
            <div className="text-right">
              <span className={`badge badge-xs ${
                c.severity === 'high'   ? 'badge-error' :
                c.severity === 'medium' ? 'badge-warning' : 'badge-ghost'
              }`}>
                {c.severity}
              </span>
              <p className="text-[10px] text-base-content/40 mt-0.5">Shadow ${c.shadow}/MWh</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <progress
              className={`progress flex-1 h-1.5 ${
                c.severity === 'high'   ? 'progress-error' :
                c.severity === 'medium' ? 'progress-warning' : 'progress-success'
              }`}
              value={c.pctOfLimit}
              max={100}
            />
            <span className="text-[10px] text-base-content/40 shrink-0">{c.pctOfLimit}%</span>
          </div>
        </div>
      ))}
    </div>
  </div>
);

// ── Main view ──────────────────────────────────────────────────────────────
export const AnalyticsView: React.FC = () => {
  const [date, setDate] = useState('2025-03-15');
  const [refreshing, setRefreshing] = useState(false);
  const [activeContext, setActiveContext] = useState<AnalyticsContextId>('overview');

  const contextProps = (id: AnalyticsContextId): React.HTMLAttributes<HTMLDivElement> => ({
    onMouseEnter: () => setActiveContext(id),
    onMouseLeave: () => setActiveContext('overview'),
    onFocusCapture: () => setActiveContext(id),
    onBlurCapture: () => setActiveContext('overview'),
  });

  const handleRefresh = () => {
    setRefreshing(true);
    // TODO: Re-fetch analytics data from /api/analytics/...
    setTimeout(() => setRefreshing(false), 800);
  };

  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4 max-w-6xl">

        {/* Controls */}
        <div {...contextProps('controls')} className="flex items-center gap-3 flex-wrap">
          <label className="flex items-center gap-2 bg-base-200 border border-base-content/10
                            rounded-lg px-3 py-2 text-xs cursor-pointer hover:border-primary/40">
            <Calendar size={13} className="text-base-content/40" />
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              className="bg-transparent outline-none text-base-content text-xs cursor-pointer"
            />
          </label>
          <button
            onClick={handleRefresh}
            className="btn btn-ghost btn-xs gap-1.5 text-base-content/50 hover:text-base-content"
          >
            <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
          <span className="text-[10px] text-base-content/25 ml-auto">
            {/* TODO: show last-updated timestamp from API */}
            Last updated: {new Date().toLocaleTimeString()}
          </span>
        </div>

        {/* KPI cards */}
        <div className="flex gap-3 flex-wrap">
          {MOCK_METRICS.map(m => (
            <MetricCard key={m.label} {...m} contextProps={contextProps('kpis')} />
          ))}
        </div>

        {/* Price chart */}
        <PriceChart contextProps={contextProps('price_chart')} />

        {/* Two-column: heatmap + congestion */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <NodeHeatmap contextProps={contextProps('node_heatmap')} />
          <CongestionTable contextProps={contextProps('constraints')} />
        </div>
        </div>
      </div>
      <DashboardContextPanel
        title="Analytics"
        purpose="What happened in the market, calculated from structured data."
        activeId={activeContext}
        sections={ANALYTICS_CONTEXT}
      />
    </div>
  );
};
