/**
 * QueryCapabilities Panel
 * ──────────────────────────────────────────────────────────────────────────
 * Collapsible panel showing 4 query categories with clickable example chips.
 * Clicking a chip populates (and optionally sends) the query in InvestigationView.
 *
 * Props:
 *   onSelectQuery — called with the query text + kind when a chip is clicked.
 *   autoSend      — if true, clicking a chip auto-submits the query.
 */
import React, { useState } from 'react';
import {
  Activity, ShieldAlert, FileText, GitMerge,
  ChevronDown, ChevronUp, Sparkles,
  type LucideIcon,
} from 'lucide-react';
import { QUERY_CAPABILITY_GROUPS } from '../data/mockData';
import type { QueryCategory, QueryChip, ChatMessage } from '../types';

interface QueryCapabilitiesProps {
  onSelectQuery: (text: string, kind: ChatMessage['kind']) => void;
  autoSend?: boolean;
}

const CATEGORY_ICONS: Record<QueryCategory, LucideIcon> = {
  market:   Activity,
  exposure: ShieldAlert,
  rules:    FileText,
  hybrid:   GitMerge,
};

export const QueryCapabilities: React.FC<QueryCapabilitiesProps> = ({
  onSelectQuery,
  autoSend = false,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<QueryCategory>('market');

  const activeGroup = QUERY_CAPABILITY_GROUPS.find(g => g.id === activeTab)!;

  const handleChipClick = (chip: QueryChip) => {
    onSelectQuery(chip.text, chip.kind);
  };

  return (
    <div className={`
      mx-4 mt-4 rounded-xl border border-base-content/10 bg-base-200/80
      overflow-hidden transition-all duration-200
    `}>
      {/* ── Header ────────────────────────────────────────────────────── */}
      <button
        onClick={() => setCollapsed(c => !c)}
        className="w-full flex items-center gap-2.5 px-4 py-3 hover:bg-base-300/50 transition-colors group"
      >
        <div className="w-6 h-6 rounded-md bg-primary/15 flex items-center justify-center shrink-0">
          <Sparkles size={13} className="text-primary" />
        </div>
        <div className="flex-1 text-left">
          <p className="text-xs font-bold text-base-content">Query Capabilities</p>
          <p className="text-[10px] text-base-content/40 mt-0.5">
            4 modes - market behavior · exposure & risk · rules context · hybrid analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Category dots */}
          <div className="hidden sm:flex items-center gap-1">
            {QUERY_CAPABILITY_GROUPS.map(g => (
              <span key={g.id} className={`w-1.5 h-1.5 rounded-full ${
                g.id === 'market'   ? 'bg-blue-400' :
                g.id === 'exposure' ? 'bg-emerald-400' :
                g.id === 'rules'    ? 'bg-amber-400' :
                'bg-violet-400'
              }`} />
            ))}
          </div>
          {collapsed
            ? <ChevronDown size={14} className="text-base-content/30 group-hover:text-base-content/60 transition-colors" />
            : <ChevronUp   size={14} className="text-base-content/30 group-hover:text-base-content/60 transition-colors" />}
        </div>
      </button>

      {/* ── Body ──────────────────────────────────────────────────────── */}
      {!collapsed && (
        <div className="border-t border-base-content/8">
          {/* Tab row */}
          <div className="flex overflow-x-auto scrollbar-hide border-b border-base-content/8 bg-base-300/20">
            {QUERY_CAPABILITY_GROUPS.map(group => {
              const Icon = CATEGORY_ICONS[group.id];
              const isActive = group.id === activeTab;
              return (
                <button
                  key={group.id}
                  onClick={() => setActiveTab(group.id)}
                  className={`
                    flex items-center gap-1.5 px-4 py-2.5 shrink-0 text-xs font-medium
                    border-b-2 transition-all duration-150 whitespace-nowrap
                    ${isActive
                      ? `${group.color} ${group.bg} border-current`
                      : 'text-base-content/40 border-transparent hover:text-base-content/70 hover:bg-base-300/30'}
                  `}
                >
                  <Icon size={13} className="shrink-0" />
                  {group.label}
                </button>
              );
            })}
          </div>

          {/* Active tab content */}
          <div className="p-4">
            {/* Tagline */}
            <p className={`text-[11px] font-medium mb-3 ${activeGroup.color} opacity-80`}>
              {activeGroup.tagline}
            </p>

            {/* Query chips */}
            <div className="flex flex-col gap-2">
              {activeGroup.queries.map((chip, i) => {
                const Icon = CATEGORY_ICONS[activeGroup.id];
                return (
                  <button
                    key={i}
                    onClick={() => handleChipClick(chip)}
                    className={`
                      group flex items-start gap-2.5 w-full text-left px-3 py-2.5 rounded-lg
                      bg-base-300/40 border border-base-content/8 text-xs text-base-content/70
                      transition-all duration-150 cursor-pointer
                      hover:bg-base-300/80 hover:border-current hover:text-base-content
                      ${activeGroup.border}
                    `}
                  >
                    {/* Number badge */}
                    <span className={`
                      shrink-0 w-5 h-5 rounded-full flex items-center justify-center
                      text-[10px] font-bold mt-0.5
                      ${activeGroup.bg} ${activeGroup.color}
                    `}>
                      {i + 1}
                    </span>
                    <span className="flex-1 leading-relaxed">{chip.text}</span>
                    {/* Send arrow */}
                    <span className={`
                      shrink-0 opacity-0 group-hover:opacity-100 transition-opacity
                      text-[10px] font-bold mt-0.5 ${activeGroup.color}
                    `}>
                      {autoSend ? '⏎ send' : '↑ use'}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Footer note */}
            <p className="text-[10px] text-base-content/25 mt-3">
              Click any query to {autoSend ? 'send it directly' : 'populate the input box'} · Results use mock data
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
