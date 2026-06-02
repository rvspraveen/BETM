"""Build UI-ready visualization JSON from deterministic analytics results."""
from __future__ import annotations

from typing import Any


ChartSpec = dict[str, Any]


SERIES_COLORS = {
    "primary": "#60a5fa",
    "secondary": "#a78bfa",
    "success": "#34d399",
    "warning": "#fbbf24",
    "error": "#f87171",
    "neutral": "#94a3b8",
}


def build_visualizations(analytics_data: dict[str, Any] | None) -> list[ChartSpec]:
    """Return compact visualization specs for the final investigate metadata event."""
    if not analytics_data or analytics_data.get("error"):
        return []

    visualizations: list[ChartSpec] = []

    if price_spikes := analytics_data.get("price_spikes"):
        visualizations.extend(_price_spike_visualizations(price_spikes))

    if divergence := analytics_data.get("da_rt_divergence"):
        visualizations.extend(_da_rt_visualizations(divergence))

    if exposure := analytics_data.get("congestion_exposure"):
        visualizations.extend(_congestion_exposure_visualizations(exposure))

    if settlements := analytics_data.get("settlement_variance"):
        visualizations.extend(_settlement_visualizations(settlements))

    if load := analytics_data.get("load_forecast"):
        visualizations.extend(_load_visualizations(load))

    if generation := analytics_data.get("generation_mix"):
        visualizations.extend(_generation_visualizations(generation))

    if pnl := analytics_data.get("pnl_summary"):
        visualizations.extend(_pnl_visualizations(pnl))

    return visualizations[:6]


def _price_spike_visualizations(result: dict[str, Any]) -> list[ChartSpec]:
    spikes = result.get("spikes") or []
    top = spikes[:8]
    if not top:
        return []

    peak = max(top, key=lambda row: _num(row.get("lmp")))
    return [
        {
            "id": "price_spike_summary",
            "type": "kpi",
            "title": "Price Spike Summary",
            "description": f"{result.get('market', 'RT')} intervals above ${result.get('threshold', 0)}/MWh.",
            "metrics": [
                {"label": "Spike Count", "value": str(result.get("count", len(spikes))), "tone": "warning"},
                {"label": "Peak LMP", "value": _money(peak.get("lmp")), "detail": peak.get("node_id"), "tone": "error"},
                {"label": "Peak Congestion", "value": _money(peak.get("congestion")), "tone": "warning"},
            ],
        },
        {
            "id": "price_spike_top_nodes",
            "type": "bar",
            "title": "Top Price Spike Intervals",
            "description": "Highest LMP rows from the selected market window.",
            "data": [
                {
                    "node": row.get("node_id"),
                    "lmp": _round(row.get("lmp")),
                    "congestion": _round(row.get("congestion")),
                }
                for row in top
            ],
            "xKey": "node",
            "unit": "$/MWh",
            "yKeys": [
                {"key": "lmp", "label": "LMP", "color": SERIES_COLORS["error"]},
                {"key": "congestion", "label": "Congestion", "color": SERIES_COLORS["warning"]},
            ],
        },
    ]


def _da_rt_visualizations(result: dict[str, Any]) -> list[ChartSpec]:
    records = (result.get("records") or [])[:10]
    if not records:
        return []
    return [
        {
            "id": "da_rt_divergence",
            "type": "bar",
            "title": "DA/RT Divergence",
            "description": "Largest absolute real-time minus day-ahead spreads.",
            "data": [
                {
                    "node": row.get("node_id"),
                    "da_lmp": _round(row.get("da_lmp")),
                    "rt_lmp": _round(row.get("rt_lmp")),
                    "divergence": _round(row.get("divergence")),
                }
                for row in records
            ],
            "xKey": "node",
            "unit": "$/MWh",
            "yKeys": [
                {"key": "da_lmp", "label": "DA", "color": SERIES_COLORS["primary"]},
                {"key": "rt_lmp", "label": "RT", "color": SERIES_COLORS["secondary"]},
                {"key": "divergence", "label": "Spread", "color": SERIES_COLORS["warning"]},
            ],
        }
    ]


def _congestion_exposure_visualizations(result: dict[str, Any]) -> list[ChartSpec]:
    records = (result.get("records") or [])[:10]
    if not records:
        return []
    return [
        {
            "id": "congestion_exposure",
            "type": "bar",
            "title": "Congestion Exposure",
            "description": "Book and node exposure ranked by congestion impact.",
            "data": [
                {
                    "node": row.get("node_id"),
                    "book": row.get("book"),
                    "exposure": _round(row.get("exposure")),
                    "total_mw": _round(row.get("total_mw")),
                }
                for row in records
            ],
            "xKey": "node",
            "unit": "$",
            "yKeys": [
                {"key": "exposure", "label": "Exposure", "color": SERIES_COLORS["warning"]},
                {"key": "total_mw", "label": "MW", "color": SERIES_COLORS["primary"]},
            ],
        }
    ]


def _settlement_visualizations(result: dict[str, Any]) -> list[ChartSpec]:
    records = (result.get("records") or [])[:10]
    if not records:
        return []
    return [
        {
            "id": "settlement_variance",
            "type": "bar",
            "title": "Settlement Variance",
            "description": "Largest net DA/RT settlement variance by book and node.",
            "data": [
                {
                    "node": row.get("node_id"),
                    "book": row.get("book"),
                    "net": _round(row.get("net")),
                    "total_da": _round(row.get("total_da")),
                    "total_rt": _round(row.get("total_rt")),
                }
                for row in records
            ],
            "xKey": "node",
            "unit": "$",
            "yKeys": [
                {"key": "net", "label": "Net", "color": SERIES_COLORS["secondary"]},
            ],
        }
    ]


def _load_visualizations(result: dict[str, Any]) -> list[ChartSpec]:
    records = result.get("records") or []
    if not records:
        return []
    return [
        {
            "id": "load_forecast_accuracy",
            "type": "bar",
            "title": "Load Forecast vs Actual",
            "description": "Average forecast, actual load, and absolute forecast error by zone.",
            "data": [
                {
                    "zone": row.get("zone"),
                    "forecast": _round(row.get("avg_forecast_mw")),
                    "actual": _round(row.get("avg_actual_mw")),
                    "mae": _round(row.get("mae_mw")),
                }
                for row in records
            ],
            "xKey": "zone",
            "unit": "MW",
            "yKeys": [
                {"key": "forecast", "label": "Forecast", "color": SERIES_COLORS["primary"]},
                {"key": "actual", "label": "Actual", "color": SERIES_COLORS["success"]},
                {"key": "mae", "label": "MAE", "color": SERIES_COLORS["warning"]},
            ],
        }
    ]


def _generation_visualizations(result: dict[str, Any]) -> list[ChartSpec]:
    records = result.get("records") or []
    if not records:
        return []
    return [
        {
            "id": "generation_mix",
            "type": "pie",
            "title": "Generation Mix",
            "description": "Average generation by fuel type in the selected window.",
            "data": [
                {
                    "fuel": row.get("fuel_type"),
                    "generation": _round(row.get("avg_generation_mw")),
                }
                for row in records
            ],
            "xKey": "fuel",
            "unit": "MW",
            "yKeys": [
                {"key": "generation", "label": "Generation", "color": SERIES_COLORS["primary"]},
            ],
        }
    ]


def _pnl_visualizations(result: dict[str, Any]) -> list[ChartSpec]:
    records = (result.get("records") or [])[:10]
    if not records:
        return []
    return [
        {
            "id": "pnl_summary",
            "type": "bar",
            "title": "P&L by Strategy",
            "description": "Total P&L ranked by book and strategy.",
            "data": [
                {
                    "strategy": f"{row.get('book')} / {row.get('strategy')}",
                    "total_pnl": _round(row.get("total_pnl")),
                    "realized_pnl": _round(row.get("realized_pnl")),
                }
                for row in records
            ],
            "xKey": "strategy",
            "unit": "$",
            "yKeys": [
                {"key": "total_pnl", "label": "Total P&L", "color": SERIES_COLORS["success"]},
                {"key": "realized_pnl", "label": "Realized", "color": SERIES_COLORS["primary"]},
            ],
        }
    ]


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _round(value: Any) -> float:
    return round(_num(value), 2)


def _money(value: Any) -> str:
    return f"${_round(value):,.2f}"
