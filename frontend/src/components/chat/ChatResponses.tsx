/**
 * Rich AI response renderers — one per query kind.
 * TODO: Replace mock data with live API responses from the backend.
 */
import React from 'react';
import {
  KPIRow, CauseTimeline, DARTBarChart, DataTable,
  SpreadSparkline, RecommendationBox, SourcePills, ConfidenceBadge,
} from './RichComponents';
import type { ChatMessage } from '../../types';

// ── Price Spike Response ──────────────────────────────────────────────────
export const PriceSpikeResponse: React.FC = () => (
  <div className="fade-up">
    <p className="text-sm text-base-content/80 mb-3 leading-relaxed">
      The <strong className="text-base-content">$287/MWh</strong> DA/RT spread at <strong className="text-base-content">HB_NORTH on 2025-03-15 HE14</strong> was driven by a combination of transmission constraint binding and unexpected wind curtailment. Here's the full root-cause breakdown:
    </p>

    <KPIRow cards={[
      { label: 'Peak RT Price',  value: '$287.4',  delta: '+$233 vs DA', positive: false },
      { label: 'DA Price',       value: '$54.2',   },
      { label: 'Shadow Price',   value: '$198.7',  delta: 'CORYCELL_138', positive: false },
      { label: 'P&L Impact',     value: '+$104.9K', delta: 'Book North long', positive: true },
    ]} />

    <CauseTimeline events={[
      { time: '12:15', label: 'Wind curtailment alert issued', detail: 'ERCOT issued O/C notice for West zone — 1,240 MW curtailed ahead of congested path.', type: 'warning' },
      { time: '13:00', label: 'CORYCELL_138KV binds at 94%', detail: 'Constraint shadow price reaches $145/MWh. DA schedules frozen from prior day.', type: 'warning' },
      { time: '14:00', label: 'HE14 RT price spikes', detail: 'RT LMP at HB_NORTH hits $287.4/MWh. DA/RT spread of $233.2 creates significant imbalance.', type: 'warning' },
      { time: '15:30', label: 'Constraint releases', detail: 'CORYCELL_138KV returns to 78% utilization. RT prices normalize toward DA.', type: 'success' },
    ]} />

    <DARTBarChart title="HB_NORTH — DA vs RT by Hour (HE12–HE18)" data={[
      { label: 'HE12', da: 51, rt: 53 },
      { label: 'HE13', da: 53, rt: 78 },
      { label: 'HE14', da: 54, rt: 287 },
      { label: 'HE15', da: 54, rt: 142 },
      { label: 'HE16', da: 52, rt: 67 },
      { label: 'HE17', da: 50, rt: 55 },
      { label: 'HE18', da: 49, rt: 51 },
    ]} />

    <DataTable
      headers={['Node', 'DA ($)', 'RT ($)', 'Spread ($)', 'Constraint']}
      rows={[
        { 'Node': 'HB_NORTH',     'DA ($)': 54.2,  'RT ($)': 287.4, 'Spread ($)': 233.2, 'Constraint': 'CORYCELL_138' },
        { 'Node': 'CORYCELL_138', 'DA ($)': 38.7,  'RT ($)': 189.2, 'Spread ($)': 150.5, 'Constraint': 'CORYCELL_138' },
        { 'Node': 'HB_WEST',      'DA ($)': 49.1,  'RT ($)': 61.3,  'Spread ($)': 12.2,  'Constraint': 'LAMAR_345'    },
        { 'Node': 'HB_HOUSTON',   'DA ($)': 55.8,  'RT ($)': 62.4,  'Spread ($)': 6.6,   'Constraint': 'None'         },
      ]}
      highlightCol="Spread ($)"
    />

    <p className="text-xs text-base-content/50 mb-2">Spread over 24 hours — HB_NORTH</p>
    <SpreadSparkline values={[2, 3, 4, 8, 25, 233, 88, 15, 8, 5, 3, 2, 1, 1, 2, 3, 4, 3, 2, 2, 1, 1, 1, 1]} />

    <RecommendationBox items={[
      'Review Book North long position — current $104.9K gain should be locked via settlement nomination.',
      'Flag CORYCELL_138KV for transmission planning — 14/21 binding days indicates structural constraint.',
      'Set DA/RT spread alert threshold at $50/MWh for HB_NORTH to enable proactive hedging.',
    ]} />

    <SourcePills sources={['ERCOT RT LMP Feed', 'Congestion DB', 'Protocol §6.5.7', 'Outage OTG-2025-0312']} />
    <div className="mt-2"><ConfidenceBadge score={0.94} /></div>
  </div>
);

// ── Settlement Variance Response ──────────────────────────────────────────
export const SettlementVarianceResponse: React.FC = () => (
  <div className="fade-up">
    <p className="text-sm text-base-content/80 mb-3 leading-relaxed">
      Settlement variances exceeding <strong className="text-base-content">$50K</strong> were found across <strong className="text-base-content">3 books</strong> for the period. Total exposure is <strong className="text-error">$127,400</strong>. Primary driver is unscheduled outage documentation mismatch.
    </p>

    <KPIRow cards={[
      { label: 'Total Variance',  value: '$127.4K', delta: '3 books affected', positive: false },
      { label: 'Largest Single',  value: '$73.4K',  delta: 'Book Houston',     positive: false },
      { label: 'Doc Match Rate',  value: '67%',     delta: '33% unresolved',   positive: false },
      { label: 'Pending Review',  value: '2 items', delta: 'Requires action',  positive: false },
    ]} />

    <DataTable
      headers={['Book', 'Node', 'Variance ($)', 'Driver', 'Doc Match']}
      rows={[
        { 'Book': 'Houston', 'Node': 'WOODLANDS_69',  'Variance ($)': 41200,  'Driver': 'Outage OTG-2025-0312', 'Doc Match': 'Partial' },
        { 'Book': 'Houston', 'Node': 'HB_HOUSTON',    'Variance ($)': 32200,  'Driver': 'RT deviation HE14',    'Doc Match': 'Yes'     },
        { 'Book': 'North',   'Node': 'HB_NORTH',      'Variance ($)': 28400,  'Driver': 'Constraint CORYCELL',  'Doc Match': 'Yes'     },
        { 'Book': 'West',    'Node': 'ABILENE_138',   'Variance ($)': 14200,  'Driver': 'Load forecast error',  'Doc Match': 'No'      },
        { 'Book': 'South',   'Node': 'LAREDO_345',    'Variance ($)': 11400,  'Driver': 'Generation ramp',      'Doc Match': 'Yes'     },
      ]}
      highlightCol="Variance ($)"
    />

    <RecommendationBox items={[
      'WOODLANDS_69: Timing mismatch of 23 min between outage data and ERCOT Notice #4821 requires manual verification before settlement submission.',
      'ABILENE_138: No supporting documentation found — open a data quality ticket and hold settlement.',
      'Consider automating outage-notice cross-reference checks at T-2h before settlement cutoff.',
    ]} />

    <SourcePills sources={['Settlement DB', 'ERCOT Notice #4821', 'Outage Registry', 'Protocol §9.3.2']} />
    <div className="mt-2"><ConfidenceBadge score={0.81} /></div>
  </div>
);

// ── Document Query Response ───────────────────────────────────────────────
export const DocQueryResponse: React.FC<{ query: string }> = ({ query }) => (
  <div className="fade-up">
    <p className="text-sm text-base-content/80 mb-3 leading-relaxed">
      Searching ERCOT protocol library and market notices for: <em className="text-primary/80">"{query}"</em>
    </p>

    <div className="space-y-2 my-3">
      {[
        { title: 'ERCOT Nodal Protocol §6.5 — Congestion Management', relevance: 97, snippet: 'Defines CRR allocation, shadow pricing methodology, and real-time re-dispatch procedures for binding transmission constraints...' },
        { title: 'ERCOT Settlement Protocol §9.3 — Make-Whole Payments', relevance: 91, snippet: 'Covers settlement adjustment procedures including Day-Ahead to Real-Time imbalance settlement, resettlement timelines, and dispute resolution...' },
        { title: 'Market Notice #4821 — Transmission Outage Procedure', relevance: 88, snippet: 'Establishes reporting requirements for unscheduled transmission outages affecting nodal price formation, including minimum notification lead times...' },
        { title: 'ERCOT Operating Guide §3.2.4 — LMP Calculation', relevance: 84, snippet: 'Specifies the decomposition of LMP into energy, congestion, and loss components for both DA and RT settlement intervals...' },
      ].map((doc, i) => (
        <div key={i} className="rounded-lg border border-base-content/10 bg-base-300/30 p-3">
          <div className="flex items-start justify-between gap-2 mb-1">
            <span className="text-xs font-semibold text-base-content">{doc.title}</span>
            <span className="shrink-0 text-[10px] font-bold text-success bg-success/10 px-1.5 py-0.5 rounded">
              {doc.relevance}%
            </span>
          </div>
          <p className="text-xs text-base-content/50 leading-relaxed">{doc.snippet}</p>
        </div>
      ))}
    </div>

    <SourcePills sources={['Protocol §6.5', 'Protocol §9.3', 'Market Notice #4821', 'Operating Guide §3.2.4']} />
    <div className="mt-2"><ConfidenceBadge score={0.93} /></div>
  </div>
);

// ── Analytics Query Response ──────────────────────────────────────────────
export const AnalyticsQueryResponse: React.FC<{ query: string }> = ({ query }) => (
  <div className="fade-up">
    <p className="text-sm text-base-content/80 mb-3 leading-relaxed">
      Running structured query: <em className="text-emerald-400/80">"{query}"</em>
    </p>

    <KPIRow cards={[
      { label: 'Nodes Analyzed', value: '847',      delta: 'ERCOT-wide' },
      { label: 'Max Spread',     value: '$233/MWh',  delta: 'HB_NORTH HE14', positive: false },
      { label: 'Avg Spread',     value: '$8.73',     delta: '+$2.10 wow' },
      { label: 'Constrained %',  value: '23.4%',     delta: 'of hub hours',  positive: false },
    ]} />

    <DataTable
      headers={['Rank', 'Node', 'Avg Spread', 'Max Spread', 'Hours > $50']}
      rows={[
        { 'Rank': 1, 'Node': 'HB_NORTH',     'Avg Spread': '$42.1', 'Max Spread': '$233', 'Hours > $50': 8  },
        { 'Rank': 2, 'Node': 'CORYCELL_138', 'Avg Spread': '$31.7', 'Max Spread': '$189', 'Hours > $50': 6  },
        { 'Rank': 3, 'Node': 'LAMAR_345',    'Avg Spread': '$12.4', 'Max Spread': '$74',  'Hours > $50': 2  },
        { 'Rank': 4, 'Node': 'HB_WEST',      'Avg Spread': '$8.2',  'Max Spread': '$41',  'Hours > $50': 0  },
        { 'Rank': 5, 'Node': 'HB_HOUSTON',   'Avg Spread': '$6.1',  'Max Spread': '$28',  'Hours > $50': 0  },
      ]}
      highlightCol="Avg Spread"
    />

    <SourcePills sources={['Price DB', 'DA LMP Archive', 'RT LMP Feed', '7-day window']} />
    <div className="mt-2"><ConfidenceBadge score={0.98} /></div>
  </div>
);

// ── Hybrid Query Response ─────────────────────────────────────────────────
export const HybridQueryResponse: React.FC<{ query: string }> = ({ query }) => (
  <div className="fade-up">
    <p className="text-sm text-base-content/80 mb-3 leading-relaxed">
      Fusing structured data with document context for: <em className="text-violet-400/80">"{query}"</em>
    </p>

    <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-3 mb-3 text-xs text-base-content/70">
      <span className="font-semibold text-violet-400">Data sources joined: </span>
      RT LMP prices ⟶ Congestion events ⟶ Outage registry ⟶ Protocol §6.5.7 ⟶ Market notices
    </div>

    <CauseTimeline events={[
      { time: 'HE18', label: 'Initial congestion onset',  detail: 'CORYCELL_138KV reaches 87% utilization. Shadow price $82/MWh. No protocol action required yet.', type: 'info' },
      { time: 'HE19', label: 'Protocol threshold breach', detail: 'Shadow price exceeds $100/MWh per §6.5.7 threshold. ERCOT initiates re-dispatch of 340 MW.', type: 'warning' },
      { time: 'HE20', label: 'Outage OTG-2025-0318 starts', detail: 'Unscheduled outage reduces path capacity 18%. RT prices accelerate to $167/MWh.', type: 'warning' },
      { time: 'HE21', label: 'Peak congestion', detail: 'Shadow price $198.7/MWh. 3 operational notices issued. Market Notice #4821 cross-reference confirmed.', type: 'warning' },
    ]} />

    <RecommendationBox items={[
      'Root cause confirmed: overlapping constraint + unscheduled outage — not forecasting error.',
      'Settlement adjustment warranted per Protocol §9.3.2 — file dispute within 30 days.',
      'Two similar historical events (2024-08-22, 2024-11-04) resulted in resettlement credits averaging $38K.',
    ]} />

    <SourcePills sources={['RT LMP Feed', 'Outage OTG-2025-0318', 'Protocol §6.5.7', 'Notice #4821', 'Historical DB']} />
    <div className="mt-2"><ConfidenceBadge score={0.87} /></div>
  </div>
);

// ── Uncertainty Response ──────────────────────────────────────────────────
export const UncertaintyResponse: React.FC<{ query: string }> = ({ query }) => (
  <div className="fade-up">
    <p className="text-sm text-base-content/80 mb-3 leading-relaxed">
      Detected a data conflict or ambiguity scenario: <em className="text-amber-400/80">"{query}"</em>
    </p>

    <div className="rounded-lg border border-amber-500/30 bg-amber-500/8 p-3 mb-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-bold text-amber-400">⚠ Uncertainty Detected</span>
        <span className="text-[10px] text-base-content/40">Confidence reduced — human review recommended</span>
      </div>
      <div className="space-y-2 text-xs text-base-content/70">
        <div className="flex gap-2">
          <span className="text-amber-400 shrink-0">Conflict:</span>
          <span>Outage registry shows start time 13:47 UTC; Market Notice #4821 states 14:10 UTC — 23-minute discrepancy exceeds auto-reconciliation threshold of 15 minutes.</span>
        </div>
        <div className="flex gap-2">
          <span className="text-amber-400 shrink-0">Impact:</span>
          <span>2 settlement intervals (HE14 partial) cannot be auto-settled. Estimated exposure: $18,200.</span>
        </div>
        <div className="flex gap-2">
          <span className="text-amber-400 shrink-0">Protocol:</span>
          <span>Per §9.3.5, conflicting timestamps with delta &gt;15 min must be routed to human review before settlement submission.</span>
        </div>
      </div>
    </div>

    <RecommendationBox items={[
      'DO NOT auto-approve this settlement — route to Review Queue with amber flag.',
      'Contact ERCOT operations to request confirmation of outage start time (OTG-2025-0318).',
      'Hold settlement for affected intervals until timestamp discrepancy is resolved.',
      'Document resolution outcome for audit trail per compliance requirement CMR-2025-Q1.',
    ]} />

    <SourcePills sources={['Outage Registry', 'Market Notice #4821', 'Protocol §9.3.5', 'Compliance CMR-2025-Q1']} />
    <div className="mt-2"><ConfidenceBadge score={0.52} /></div>
  </div>
);

// ── Response dispatcher ───────────────────────────────────────────────────
export const RichResponse: React.FC<{ message: ChatMessage }> = ({ message }) => {
  switch (message.kind) {
    case 'price_spike':         return <PriceSpikeResponse />;
    case 'settlement_variance': return <SettlementVarianceResponse />;
    case 'doc_query':           return <DocQueryResponse query={message.text ?? ''} />;
    case 'analytics_query':     return <AnalyticsQueryResponse query={message.text ?? ''} />;
    case 'hybrid_query':        return <HybridQueryResponse query={message.text ?? ''} />;
    case 'uncertainty_query':   return <UncertaintyResponse query={message.text ?? ''} />;
    default:
      return <p className="text-sm text-base-content/80 leading-relaxed whitespace-pre-line">{message.text}</p>;
  }
};
