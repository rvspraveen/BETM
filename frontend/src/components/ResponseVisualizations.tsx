import React from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type {
  InvestigationVisualization,
  VisualizationColumn,
  VisualizationMetric,
  VisualizationSeries,
} from '../types';

const FALLBACK_COLORS = ['#60a5fa', '#a78bfa', '#34d399', '#fbbf24', '#f87171', '#94a3b8'];

const toneClass: Record<NonNullable<VisualizationMetric['tone']>, string> = {
  neutral: 'border-base-content/10 bg-base-100/60 text-base-content',
  success: 'border-success/25 bg-success/10 text-success',
  warning: 'border-warning/25 bg-warning/10 text-warning',
  error: 'border-error/25 bg-error/10 text-error',
};

interface ResponseVisualizationsProps {
  items?: InvestigationVisualization[];
}

export function ResponseVisualizations({ items }: ResponseVisualizationsProps) {
  const visibleItems = (items ?? []).filter(item => {
    if (item.type === 'kpi') return item.metrics?.length;
    return item.data?.length;
  });

  if (!visibleItems.length) return null;

  return (
    <div className="mt-4 space-y-3">
      {visibleItems.map(item => (
        <VisualizationCard key={item.id} item={item} />
      ))}
    </div>
  );
}

function VisualizationCard({ item }: { item: InvestigationVisualization }) {
  return (
    <section className="rounded-xl border border-base-content/10 bg-base-100/65 p-3 shadow-sm">
      <div className="mb-2">
        <p className="text-sm font-semibold text-base-content">{item.title}</p>
        {item.description && (
          <p className="mt-0.5 text-xs leading-relaxed text-base-content/55">{item.description}</p>
        )}
      </div>
      {item.type === 'kpi' && <KpiGrid metrics={item.metrics ?? []} />}
      {item.type === 'bar' && <BarVisualization item={item} />}
      {item.type === 'line' && <LineVisualization item={item} />}
      {item.type === 'pie' && <PieVisualization item={item} />}
      {item.type === 'table' && <TableVisualization item={item} />}
    </section>
  );
}

function KpiGrid({ metrics }: { metrics: VisualizationMetric[] }) {
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {metrics.map(metric => (
        <div
          key={`${metric.label}-${metric.value}`}
          className={`rounded-lg border px-3 py-2 ${toneClass[metric.tone ?? 'neutral']}`}
        >
          <p className="text-[10px] font-semibold uppercase tracking-wider opacity-60">{metric.label}</p>
          <p className="mt-1 text-lg font-bold">{metric.value}</p>
          {metric.detail && <p className="mt-0.5 truncate text-xs opacity-60">{metric.detail}</p>}
        </div>
      ))}
    </div>
  );
}

function BarVisualization({ item }: { item: InvestigationVisualization }) {
  const data = item.data ?? [];
  const series = getSeries(item);
  const xKey = item.xKey ?? inferXKey(data);

  return (
    <ChartShell>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.22)" vertical={false} />
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 10, fill: 'currentColor' }}
          tickFormatter={truncateTick}
          interval={0}
        />
        <YAxis tick={{ fontSize: 10, fill: 'currentColor' }} width={48} />
        <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} formatter={formatTooltip(item.unit)} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {series.map((entry, index) => (
          <Bar
            key={entry.key}
            dataKey={entry.key}
            name={entry.label}
            fill={entry.color ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ChartShell>
  );
}

function LineVisualization({ item }: { item: InvestigationVisualization }) {
  const data = item.data ?? [];
  const series = getSeries(item);
  const xKey = item.xKey ?? inferXKey(data);

  return (
    <ChartShell>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.22)" vertical={false} />
        <XAxis dataKey={xKey} tick={{ fontSize: 10, fill: 'currentColor' }} tickFormatter={truncateTick} />
        <YAxis tick={{ fontSize: 10, fill: 'currentColor' }} width={48} />
        <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} formatter={formatTooltip(item.unit)} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {series.map((entry, index) => (
          <Line
            key={entry.key}
            type="monotone"
            dataKey={entry.key}
            name={entry.label}
            stroke={entry.color ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ChartShell>
  );
}

function PieVisualization({ item }: { item: InvestigationVisualization }) {
  const data = item.data ?? [];
  const xKey = item.xKey ?? inferXKey(data);
  const valueKey = item.yKeys?.[0]?.key ?? inferValueKey(data, xKey);

  return (
    <ChartShell>
      <PieChart>
        <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipLabelStyle} formatter={formatTooltip(item.unit)} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Pie
          data={data}
          dataKey={valueKey}
          nameKey={xKey}
          innerRadius={48}
          outerRadius={82}
          paddingAngle={2}
        >
          {data.map((_, index) => (
            <Cell key={index} fill={FALLBACK_COLORS[index % FALLBACK_COLORS.length]} />
          ))}
        </Pie>
      </PieChart>
    </ChartShell>
  );
}

function TableVisualization({ item }: { item: InvestigationVisualization }) {
  const data = item.data ?? [];
  const columns = item.columns?.length ? item.columns : inferColumns(data);

  return (
    <div className="max-h-64 overflow-auto rounded-lg border border-base-content/10">
      <table className="table table-xs w-full">
        <thead className="sticky top-0 bg-base-200">
          <tr>
            {columns.map(column => (
              <th key={column.key} className="text-[10px] uppercase tracking-wider text-base-content/45">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map(column => (
                <td key={column.key}>{formatCell(row[column.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartShell({ children }: { children: React.ReactElement }) {
  return (
    <div className="h-64 min-w-[280px] text-base-content/70">
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
}

function getSeries(item: InvestigationVisualization): VisualizationSeries[] {
  if (item.yKeys?.length) return item.yKeys;
  const data = item.data ?? [];
  const xKey = item.xKey ?? inferXKey(data);
  const valueKey = inferValueKey(data, xKey);
  return [{ key: valueKey, label: valueKey }];
}

function inferXKey(data: Record<string, unknown>[]): string {
  const first = data[0] ?? {};
  return Object.keys(first).find(key => typeof first[key] === 'string') ?? Object.keys(first)[0] ?? 'name';
}

function inferValueKey(data: Record<string, unknown>[], xKey: string): string {
  const first = data[0] ?? {};
  return Object.keys(first).find(key => key !== xKey && typeof first[key] === 'number') ?? Object.keys(first)[1] ?? 'value';
}

function inferColumns(data: Record<string, unknown>[]): VisualizationColumn[] {
  return Object.keys(data[0] ?? {}).map(key => ({ key, label: key.replace(/_/g, ' ') }));
}

function truncateTick(value: unknown): string {
  const text = String(value ?? '');
  return text.length > 12 ? `${text.slice(0, 10)}...` : text;
}

function formatCell(value: unknown): string {
  if (typeof value === 'number') return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(value ?? '');
}

function formatTooltip(unit?: string) {
  return (value: unknown, name: unknown) => {
    const formatted = typeof value === 'number'
      ? formatNumberWithUnit(value, unit)
      : String(value ?? '');
    return [formatted, String(name ?? '')];
  };
}

function formatNumberWithUnit(value: number, unit?: string): string {
  const formatted = value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (unit === '$') return `$${formatted}`;
  if (unit === '$/MWh') return `$${formatted}/MWh`;
  return unit ? `${formatted} ${unit}` : formatted;
}

const tooltipStyle = {
  background: 'hsl(var(--b1))',
  border: '1px solid hsl(var(--bc) / 0.12)',
  borderRadius: 8,
  color: 'hsl(var(--bc))',
};

const tooltipLabelStyle = {
  color: 'hsl(var(--bc) / 0.7)',
  fontSize: 12,
};
