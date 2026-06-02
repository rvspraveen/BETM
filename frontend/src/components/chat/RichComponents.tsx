/**
 * Shared rich-response sub-components used inside AI messages.
 */
import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Lightbulb, ExternalLink } from 'lucide-react';

// ── KPI Card Row ──────────────────────────────────────────────────────────
interface KPICardProps { label: string; value: string; delta?: string; positive?: boolean; }
export const KPICard: React.FC<KPICardProps> = ({ label, value, delta, positive }) => (
  <div className="flex-1 min-w-[110px] rounded-lg bg-base-300/60 border border-base-content/8 p-3">
    <p className="text-[10px] text-base-content/50 mb-1 uppercase tracking-wider">{label}</p>
    <p className="text-base font-bold text-base-content">{value}</p>
    {delta && (
      <div className={`flex items-center gap-0.5 mt-0.5 text-xs font-medium
        ${positive ? 'text-success' : 'text-error'}`}>
        {positive
          ? <TrendingDown size={11} />
          : <TrendingUp size={11} />}
        {delta}
      </div>
    )}
  </div>
);

export const KPIRow: React.FC<{ cards: KPICardProps[] }> = ({ cards }) => (
  <div className="flex flex-wrap gap-2 my-3">
    {cards.map(c => <KPICard key={c.label} {...c} />)}
  </div>
);

// ── Cause Timeline ────────────────────────────────────────────────────────
interface TimelineEvent { time: string; label: string; detail: string; type: 'warning' | 'info' | 'success'; }
export const CauseTimeline: React.FC<{ events: TimelineEvent[] }> = ({ events }) => (
  <div className="my-3 space-y-0">
    {events.map((ev, i) => (
      <div key={i} className="flex gap-3 relative">
        {/* vertical line */}
        {i < events.length - 1 && (
          <div className="absolute left-[11px] top-6 bottom-0 w-px bg-base-content/10" />
        )}
        <div className={`shrink-0 w-5 h-5 mt-0.5 rounded-full flex items-center justify-center
          ${ev.type === 'warning' ? 'bg-warning/20 text-warning'
            : ev.type === 'success' ? 'bg-success/20 text-success'
            : 'bg-info/20 text-info'}`}>
          {ev.type === 'warning' ? <AlertTriangle size={10} />
            : ev.type === 'success' ? <CheckCircle size={10} />
            : <div className="w-1.5 h-1.5 rounded-full bg-info" />}
        </div>
        <div className="pb-3">
          <div className="flex items-baseline gap-2">
            <span className="text-xs font-mono text-base-content/40">{ev.time}</span>
            <span className="text-xs font-semibold text-base-content">{ev.label}</span>
          </div>
          <p className="text-xs text-base-content/60 mt-0.5">{ev.detail}</p>
        </div>
      </div>
    ))}
  </div>
);

// ── Bar Chart (DA vs RT) ──────────────────────────────────────────────────
interface BarData { label: string; da: number; rt: number; }
export const DARTBarChart: React.FC<{ data: BarData[]; title?: string }> = ({ data, title }) => {
  const maxVal = Math.max(...data.flatMap(d => [d.da, d.rt]), 1);
  return (
    <div className="my-3 rounded-lg bg-base-300/40 p-3 border border-base-content/8">
      {title && <p className="text-xs font-semibold text-base-content/60 mb-2">{title}</p>}
      <div className="flex items-end gap-1.5 h-28">
        {data.map(d => (
          <div key={d.label} className="flex-1 flex flex-col items-center gap-0.5">
            <div className="w-full flex gap-0.5 items-end h-24">
              <div className="flex-1 rounded-t bg-primary/60" style={{ height: `${(d.da / maxVal) * 100}%` }} />
              <div className="flex-1 rounded-t bg-secondary/60" style={{ height: `${(d.rt / maxVal) * 100}%` }} />
            </div>
            <span className="text-[9px] text-base-content/40">{d.label}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-3 mt-2 justify-end">
        <span className="flex items-center gap-1 text-[10px] text-base-content/50">
          <span className="w-2 h-2 rounded-sm bg-primary/60 inline-block" /> DA
        </span>
        <span className="flex items-center gap-1 text-[10px] text-base-content/50">
          <span className="w-2 h-2 rounded-sm bg-secondary/60 inline-block" /> RT
        </span>
      </div>
    </div>
  );
};

// ── Data Table ────────────────────────────────────────────────────────────
interface TableRow { [key: string]: string | number | boolean; }
export const DataTable: React.FC<{
  headers: string[];
  rows: TableRow[];
  highlightCol?: string;
}> = ({ headers, rows, highlightCol }) => (
  <div className="my-3 overflow-x-auto rounded-lg border border-base-content/10">
    <table className="table table-xs w-full">
      <thead>
        <tr className="bg-base-300/80">
          {headers.map(h => (
            <th key={h} className="text-[10px] uppercase tracking-wider text-base-content/40 font-semibold">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className="border-base-content/5 hover:bg-base-300/30">
            {headers.map(h => {
              const val = row[h];
              const isHighlight = h === highlightCol;
              const isNeg = typeof val === 'number' && val < 0;
              const isPos = typeof val === 'number' && val > 0 && isHighlight;
              return (
                <td key={h} className={`text-xs
                  ${isHighlight && isNeg ? 'text-error font-semibold' : ''}
                  ${isHighlight && isPos ? 'text-success font-semibold' : ''}
                `}>
                  {typeof val === 'number'
                    ? (h.toLowerCase().includes('pnl') || h.toLowerCase().includes('$')
                        ? `${val >= 0 ? '+' : ''}$${Math.abs(val).toLocaleString()}`
                        : val.toLocaleString())
                    : String(val)}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// ── Spread Sparkline ──────────────────────────────────────────────────────
export const SpreadSparkline: React.FC<{ values: number[]; label?: string }> = ({ values, label }) => {
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const h = 40; const w = 200;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - min) / (max - min)) * h;
    return `${x},${y}`;
  }).join(' ');
  return (
    <div className="my-2 inline-flex flex-col gap-1">
      {label && <span className="text-[10px] text-base-content/40">{label}</span>}
      <svg viewBox={`0 0 ${w} ${h}`} className="w-40 h-8 overflow-visible">
        <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="1.5"
          className="text-primary" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

// ── Recommendation Box ────────────────────────────────────────────────────
export const RecommendationBox: React.FC<{ items: string[] }> = ({ items }) => (
  <div className="my-3 rounded-lg border border-primary/30 bg-primary/8 p-3">
    <div className="flex items-center gap-1.5 mb-2">
      <Lightbulb size={13} className="text-primary" />
      <span className="text-xs font-semibold text-primary">Recommended Actions</span>
    </div>
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={i} className="text-xs text-base-content/70 flex gap-2">
          <span className="text-primary mt-0.5 shrink-0">›</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  </div>
);

// ── Source Pills ──────────────────────────────────────────────────────────
export const SourcePills: React.FC<{ sources: string[] }> = ({ sources }) => (
  <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-base-content/8">
    <span className="text-[10px] text-base-content/30 mr-1 self-center">Sources:</span>
    {sources.map(s => (
      <span key={s} className="source-pill">
        <ExternalLink size={9} />
        {s}
      </span>
    ))}
  </div>
);

// ── Confidence Badge ──────────────────────────────────────────────────────
export const ConfidenceBadge: React.FC<{ score: number }> = ({ score }) => {
  const pct = Math.round(score * 100);
  const color = pct >= 85 ? 'text-success' : pct >= 65 ? 'text-warning' : 'text-error';
  return (
    <span className={`text-[10px] font-semibold ${color}`}>
      {pct}% confidence
    </span>
  );
};
