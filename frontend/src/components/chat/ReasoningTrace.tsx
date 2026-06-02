import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Brain } from 'lucide-react';
import type { ReasoningStep } from '../../types';

interface Props { steps: ReasoningStep[]; }

export const ReasoningTrace: React.FC<Props> = ({ steps }) => {
  const [open, setOpen] = useState(false);
  const totalMs = steps.reduce((a, s) => a + s.durationMs, 0);

  return (
    <div className="mb-3 rounded-lg border border-base-content/10 overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-base-300/50 hover:bg-base-300
                   text-xs text-base-content/50 transition-colors"
      >
        <Brain size={12} className="shrink-0 text-secondary/70" />
        <span className="flex-1 text-left font-medium">
          Reasoning trace — {steps.length} steps · {(totalMs / 1000).toFixed(1)}s
        </span>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      {open && (
        <div className="px-3 py-2 bg-base-300/20 thinking-trace">
          {steps.map((s, i) => (
            <div key={i} className="py-0.5">
              <span className="text-base-content/30 mr-2">[{(s.durationMs / 1000).toFixed(2)}s]</span>
              <span className="text-base-content/60 font-semibold">{s.label}: </span>
              <span className="text-base-content/40">{s.detail}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
