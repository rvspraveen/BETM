/**
 * Positions View — live trading book positions from /api/v1/analytics/positions
 */
import React, { useState, useEffect, useMemo } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, Filter } from 'lucide-react';
import { getPositions } from '../services/api';
import { DashboardContextPanel, ContextSection } from './DashboardContextPanel';

interface Position {
  id: number;
  trade_date: string;
  book: string;
  node_id: string;
  node_name: string;
  product: string;
  quantity_mw: number;
  avg_price: number;
  mark_price: number;
  unrealized_pnl: number;
  delta: number;
}

type SortKey = keyof Position;
type PositionsContextId = 'overview' | 'filters' | 'summary' | 'exposure' | 'pnl' | 'ledger';

const POSITIONS_CONTEXT: ContextSection[] = [
  {
    id: 'overview',
    title: 'Risk Exposure Ledger',
    summary: 'Portfolio lens for positions, exposure, and market impact.',
    datasets: ['ftr_positions.csv', 'physical_positions.csv', 'trade_pnl.csv', 'asset_metadata.csv'],
    signals: [
      'Use after Analytics finds an anomaly to see if the firm had exposure.',
    ],
  },
  {
    id: 'filters',
    title: 'Book and Product Filters',
    summary: 'Narrows the ledger by ownership and product type.',
    datasets: ['asset_metadata.csv', 'positions.csv', 'ftr_positions.csv', 'physical_positions.csv'],
    signals: [
      'Book shows who owns the exposure; product shows how it is carried.',
    ],
  },
  {
    id: 'summary',
    title: 'Portfolio Summary',
    summary: 'Count, net MW, and unrealized P&L for the current selection.',
    datasets: ['positions.csv', 'trade_pnl.csv'],
    signals: [
      'Read these cards together to separate breadth from concentration.',
    ],
  },
  {
    id: 'exposure',
    title: 'Net Quantity and Delta',
    summary: 'Directional MW exposure and price sensitivity.',
    datasets: ['physical_positions.csv', 'ftr_positions.csv', 'positions.csv'],
    signals: [
      'Compare sign and size against Analytics spikes or congested nodes.',
    ],
  },
  {
    id: 'pnl',
    title: 'Unrealized P&L',
    summary: 'Mark-to-market impact for the filtered positions.',
    datasets: ['trade_pnl.csv', 'positions.csv'],
    signals: [
      'Negative P&L should be checked against congestion and DA/RT divergence.',
    ],
  },
  {
    id: 'ledger',
    title: 'Position Ledger',
    summary: 'Sortable row-level detail for book, node, product, quantity, P&L, and delta.',
    datasets: ['positions.csv', 'asset_metadata.csv'],
    signals: [
      'Sort by P&L, quantity, or delta to find the largest exposure.',
    ],
  },
];

export default function PositionsView() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [bookFilter, setBookFilter] = useState('ALL');
  const [productFilter, setProductFilter] = useState('ALL');
  const [sortKey, setSortKey] = useState<SortKey>('unrealized_pnl');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [activeContext, setActiveContext] = useState<PositionsContextId>('overview');

  const contextProps = (id: PositionsContextId): React.HTMLAttributes<HTMLElement> => ({
    onMouseEnter: () => setActiveContext(id),
    onMouseLeave: () => setActiveContext('overview'),
    onFocusCapture: () => setActiveContext(id),
    onBlurCapture: () => setActiveContext('overview'),
  });

  const load = async (book?: string) => {
    setLoading(true);
    try {
      const data = await getPositions(book === 'ALL' ? undefined : book);
      setPositions(data);
    } catch (e) {
      console.error('Failed to load positions', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(bookFilter); }, [bookFilter]);

  const books = useMemo(() => ['ALL', ...Array.from(new Set(positions.map(p => p.book))).sort()], [positions]);
  const products = useMemo(() => ['ALL', ...Array.from(new Set(positions.map(p => p.product))).sort()], [positions]);

  const filtered = useMemo(() => {
    let ps = positions;
    if (productFilter !== 'ALL') ps = ps.filter(p => p.product === productFilter);
    return [...ps].sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey];
      const cmp = typeof av === 'number' && typeof bv === 'number'
        ? av - bv
        : String(av).localeCompare(String(bv));
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [positions, productFilter, sortKey, sortDir]);

  const totals = useMemo(() => ({
    quantity: filtered.reduce((s, p) => s + p.quantity_mw, 0),
    pnl: filtered.reduce((s, p) => s + p.unrealized_pnl, 0),
    delta: filtered.reduce((s, p) => s + p.delta, 0),
  }), [filtered]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const SortIcon = ({ k }: { k: SortKey }) =>
    sortKey === k ? <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span> : null;

  const fmtPnl = (v: number) => (
    <span className={v >= 0 ? 'text-success' : 'text-error'}>
      {v >= 0 ? '+' : ''}{v.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
    </span>
  );

  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-base-300 flex items-center gap-3 flex-wrap">
          <TrendingUp size={18} className="text-accent" />
          <h1 className="text-lg font-semibold">Positions</h1>

          <div {...contextProps('filters')} className="ml-auto flex items-center gap-2 flex-wrap">
            <Filter size={14} className="opacity-40" />
            {/* Book filter */}
            <select
              className="select select-bordered select-sm"
              value={bookFilter}
              onChange={e => setBookFilter(e.target.value)}
            >
              {books.map(b => <option key={b}>{b}</option>)}
            </select>
            {/* Product filter */}
            <select
              className="select select-bordered select-sm"
              value={productFilter}
              onChange={e => setProductFilter(e.target.value)}
            >
              {products.map(p => <option key={p}>{p}</option>)}
            </select>
            <button className="btn btn-ghost btn-xs" onClick={() => load(bookFilter)}>
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-3 px-6 py-3 border-b border-base-300">
          <div {...contextProps('summary')} className="stat bg-base-200 rounded-xl py-3 px-4">
            <div className="stat-title text-xs">Total Positions</div>
            <div className="stat-value text-xl">{filtered.length}</div>
          </div>
          <div {...contextProps('exposure')} className="stat bg-base-200 rounded-xl py-3 px-4">
            <div className="stat-title text-xs">Net Quantity</div>
            <div className={`stat-value text-xl ${totals.quantity >= 0 ? 'text-success' : 'text-error'}`}>
              {totals.quantity >= 0 ? '+' : ''}{totals.quantity.toFixed(0)} MW
            </div>
          </div>
          <div {...contextProps('pnl')} className="stat bg-base-200 rounded-xl py-3 px-4">
            <div className="stat-title text-xs">Unrealized P&L</div>
            <div className="stat-value text-xl">{fmtPnl(totals.pnl)}</div>
          </div>
        </div>

        {/* Table */}
        <div {...contextProps('ledger')} className="flex-1 overflow-auto px-4 py-2">
          {loading ? (
            <div className="flex items-center justify-center h-32 opacity-50">
              <RefreshCw size={20} className="animate-spin mr-2" /> Loading positions…
            </div>
          ) : (
            <table className="table table-sm table-zebra w-full text-xs">
              <thead className="sticky top-0 bg-base-100 z-10">
                <tr>
                  {([
                    ['trade_date', 'Date'],
                    ['book', 'Book'],
                    ['node_name', 'Node'],
                    ['product', 'Product'],
                    ['quantity_mw', 'Qty (MW)'],
                    ['avg_price', 'Avg Price'],
                    ['mark_price', 'Mark'],
                    ['unrealized_pnl', 'Unrealized P&L'],
                    ['delta', 'Delta'],
                  ] as [SortKey, string][]).map(([k, label]) => (
                    <th
                      key={k}
                      className="cursor-pointer hover:bg-base-200 select-none"
                      onClick={() => handleSort(k)}
                    >
                      {label}<SortIcon k={k} />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(p => (
                  <tr key={p.id} className="hover">
                    <td>{p.trade_date}</td>
                    <td><span className="badge badge-ghost badge-sm">{p.book}</span></td>
                    <td title={p.node_id}>{p.node_name}</td>
                    <td><span className={`badge badge-sm ${p.product === 'DA' ? 'badge-primary' : p.product === 'RT' ? 'badge-secondary' : 'badge-accent'}`}>{p.product}</span></td>
                    <td className={p.quantity_mw >= 0 ? 'text-success' : 'text-error'}>
                      {p.quantity_mw >= 0 ? '+' : ''}{p.quantity_mw.toFixed(1)}
                    </td>
                    <td>${p.avg_price.toFixed(2)}</td>
                    <td>${p.mark_price.toFixed(2)}</td>
                    <td>{fmtPnl(p.unrealized_pnl)}</td>
                    <td className={p.delta >= 0 ? 'text-success' : 'text-error'}>
                      {p.delta.toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-base-200 font-semibold">
                <tr>
                  <td colSpan={4} className="text-right text-xs opacity-60">TOTALS</td>
                  <td className={totals.quantity >= 0 ? 'text-success' : 'text-error'}>
                    {totals.quantity >= 0 ? '+' : ''}{totals.quantity.toFixed(0)}
                  </td>
                  <td colSpan={2} />
                  <td>{fmtPnl(totals.pnl)}</td>
                  <td className={totals.delta >= 0 ? 'text-success' : 'text-error'}>{totals.delta.toFixed(0)}</td>
                </tr>
              </tfoot>
            </table>
          )}
        </div>
      </div>
      <DashboardContextPanel
        title="Positions"
        purpose="How market movement affected books, nodes, products, and P&L."
        activeId={activeContext}
        sections={POSITIONS_CONTEXT}
      />
    </div>
  );
}
