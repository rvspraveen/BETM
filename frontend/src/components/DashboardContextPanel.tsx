import React from 'react';
import { Database, Target } from 'lucide-react';

export interface ContextSection {
  id: string;
  title: string;
  summary: string;
  datasets?: string[];
  signals?: string[];
  questions?: string[];
}

interface DashboardContextPanelProps {
  title: string;
  purpose: string;
  activeId: string;
  sections: ContextSection[];
}

export const DashboardContextPanel: React.FC<DashboardContextPanelProps> = ({
  title,
  purpose,
  activeId,
  sections,
}) => {
  return (
    <aside className="hidden xl:flex h-full w-72 shrink-0 flex-col border-l border-base-300 bg-base-200/45">
      <div className="border-b border-base-300 px-4 py-3">
        <p className="text-[10px] uppercase tracking-widest text-base-content/35 font-semibold">
          Context
        </p>
        <h2 className="mt-1 text-base font-semibold text-base-content">{title}</h2>
        <p className="mt-1 text-xs leading-relaxed text-base-content/55">{purpose}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
        {sections.map(section => {
          const active = section.id === activeId;
          const visibleSignals = section.signals?.slice(0, 2) ?? [];
          const visibleDatasets = section.datasets?.slice(0, 3) ?? [];
          return (
            <section
              key={section.id}
              className={`
                rounded-lg border p-2.5 transition-all duration-150
                ${active
                  ? 'border-primary/45 bg-primary/10 shadow-sm'
                  : 'border-base-content/8 bg-base-100/30 opacity-60'}
              `}
            >
              <div className="flex items-start gap-2">
                <Target size={13} className={`mt-0.5 shrink-0 ${active ? 'text-primary' : 'text-base-content/35'}`} />
                <div className="min-w-0 flex-1">
                  <h3 className={`text-xs font-semibold ${active ? 'text-base-content' : 'text-base-content/70'}`}>
                    {section.title}
                  </h3>
                  <p className="mt-1 text-[11px] leading-relaxed text-base-content/55">
                    {section.summary}
                  </p>
                </div>
              </div>

              {active && visibleDatasets.length > 0 && (
                <div className="mt-2">
                  <div className="mb-1 flex items-center gap-1.5 text-[9px] font-semibold uppercase tracking-wider text-base-content/35">
                    <Database size={11} />
                    Uses
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {visibleDatasets.map(dataset => (
                      <span key={dataset} className="rounded-md bg-base-300/60 px-1.5 py-0.5 text-[9px] text-base-content/60">
                        {dataset}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {active && visibleSignals.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {visibleSignals.map(signal => (
                    <li key={signal} className="flex gap-1.5 text-[11px] leading-relaxed text-base-content/55">
                      <span className={active ? 'text-primary' : 'text-base-content/30'}>•</span>
                      <span>{signal}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </aside>
  );
};
