"""Plotly chart builders for Ricky vs Control matchup visualizations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

ACCENT = "#e8d5b0"

CHART_LAYOUT = dict(
    plot_bgcolor="#000000",
    paper_bgcolor="#000000",
    font=dict(family="JetBrains Mono", color="#ffffff", size=12),
    xaxis=dict(gridcolor="#404040", linecolor="#404040", zerolinecolor="#404040", fixedrange=True),
    yaxis=dict(gridcolor="#404040", linecolor="#404040", zerolinecolor="#404040", fixedrange=True),
    hoverlabel=dict(
        bgcolor="#1a1a1a",
        bordercolor="#404040",
        font=dict(family="JetBrains Mono", color="#ffffff", size=12),
    ),
    legend=dict(
        font=dict(color="#ffffff"),
        bgcolor="rgba(0,0,0,0)",
        bordercolor="#404040",
        borderwidth=0,
    ),
    margin=dict(l=60, r=20, t=40, b=40),
    dragmode=False,
    hovermode="closest",
)

DATA_COLORS = ["#ff9800", "#3498db", "#9c27b0", "#00bcd4", "#e6c730", "#e84393", "#808080"]


def empty_chart_json(message: str) -> str:
    """Return a Plotly JSON figure with a centered text annotation and no data.

    Args:
        message: Text to display in the center of the empty chart.

    Returns:
        JSON string of the Plotly figure.
    """
    fig = go.Figure()
    fig.update_layout(**CHART_LAYOUT)
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=message,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=18, color="#808080"),
                xanchor="center",
                yanchor="middle",
            )
        ],
    )
    return pio.to_json(fig)


def _is_completed(m: Any) -> bool:
    """Check if a matchup has at least 5 fights in each condition."""
    wc = m["wins_control"]
    lc = m.get("losses_control", 0)
    wr = m["wins_ricky"]
    lr = m.get("losses_ricky", 0)
    return (wc + lc) >= 5 and (wr + lr) >= 5


def _wr_diff(m: Any) -> float:
    """Compute win rate difference (ricky - control) for a matchup."""
    wc = m["wins_control"]
    lc = m.get("losses_control", 0)
    wr = m["wins_ricky"]
    lr = m.get("losses_ricky", 0)

    wr_c = wc / (wc + lc) if (wc + lc) > 0 else 0.0
    wr_r = wr / (wr + lr) if (wr + lr) > 0 else 0.0
    return wr_r - wr_c


def build_paired_bar(matchups: Sequence[Any]) -> str:
    """Grouped bar chart comparing control vs ricky win rate per defender."""
    completed = [m for m in matchups if _is_completed(m)]
    if not completed:
        return empty_chart_json("No matchup data yet")

    completed.sort(key=lambda m: m["defender_name"])

    names = [m["defender_name"] for m in completed]
    ctrl_wrs = []
    ricky_wrs = []
    for m in completed:
        wc = m["wins_control"]
        lc = m.get("losses_control", 0)
        wr = m["wins_ricky"]
        lr = m.get("losses_ricky", 0)
        ctrl_wrs.append(wc / (wc + lc) * 100 if (wc + lc) > 0 else 0)
        ricky_wrs.append(wr / (wr + lr) * 100 if (wr + lr) > 0 else 0)

    fig = go.Figure()
    _hl = dict(bgcolor="#1a1a1a", bordercolor="#404040", font=dict(family="JetBrains Mono", color="#ffffff"))
    fig.add_trace(go.Bar(x=names, y=ctrl_wrs, name="control", marker_color="#808080", hoverlabel=_hl))
    fig.add_trace(go.Bar(x=names, y=ricky_wrs, name="ricky", marker_color=ACCENT, hoverlabel=_hl))

    fig.update_layout(**CHART_LAYOUT)
    fig.update_layout(
        title=dict(text="win rate by defender", x=0.5, xanchor="center"),
        barmode="group",
        yaxis_range=[0, 100],
        xaxis_title="defender",
        yaxis_title="win rate %",
    )

    return pio.to_json(fig)


def build_wr_boxplot(
    matchups: Sequence[Any],
    officer_colors: dict[str, str] | None = None,
) -> str:
    """Box plot of win rate diff distribution per officer plus pooled."""
    completed = [m for m in matchups if _is_completed(m)]
    if not completed:
        return empty_chart_json("No matchup data yet")

    grouped: dict[str, list[float]] = defaultdict(list)
    all_diffs: list[float] = []
    for m in completed:
        diff = _wr_diff(m)
        grouped[m["officer_name"]].append(diff)
        all_diffs.append(diff)

    fig = go.Figure()

    for i, (name, diffs) in enumerate(sorted(grouped.items())):
        if officer_colors and name in officer_colors:
            color = officer_colors[name]
        else:
            color = DATA_COLORS[i % len(DATA_COLORS)]
        hx = color.lstrip("#")
        r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
        fill = f"rgba({r},{g},{b},0.5)"

        fig.add_trace(
            go.Box(
                y=diffs,
                name=name,
                boxmean=True,
                fillcolor=fill,
                line=dict(color=color),
                marker=dict(color=color),
                hoverlabel=dict(bgcolor="#1a1a1a", bordercolor="#404040", font=dict(family="JetBrains Mono", color="#ffffff")),
            )
        )

    # Pooled box
    fig.add_trace(
        go.Box(
            y=all_diffs,
            name="pooled",
            boxmean=True,
            fillcolor="rgba(128,128,128,0.5)",
            line=dict(color="#808080"),
            marker=dict(color="#808080"),
            hoverlabel=dict(bgcolor="#1a1a1a", bordercolor="#404040", font=dict(family="JetBrains Mono", color="#ffffff")),
        )
    )

    fig.add_hline(y=0, line_dash="dash", line_color="#404040", line_width=2)

    fig.update_layout(**CHART_LAYOUT)
    fig.update_layout(
        title=dict(text="win rate diff distribution", x=0.5, xanchor="center"),
        showlegend=False,
        xaxis_title="attacker",
        yaxis_title="wr diff (ricky - control)",
    )

    return pio.to_json(fig)


def build_trophy_scatter(
    matchups: Sequence[Any],
    officer_colors: dict[str, str] | None = None,
) -> str:
    """Scatter plot of defender trophies vs win rate diff with OLS trend."""
    completed = [
        m for m in matchups
        if _is_completed(m) and m.get("defender_trophies") is not None
    ]

    if not completed:
        return empty_chart_json("add trophy data via admin to enable this chart")

    officer_matchups: dict[str, list[Any]] = defaultdict(list)
    for m in completed:
        officer_matchups[m["officer_name"]].append(m)

    all_x: list[float] = []
    all_y: list[float] = []

    fig = go.Figure()

    for i, (officer, o_matchups) in enumerate(sorted(officer_matchups.items())):
        xs: list[float] = []
        ys: list[float] = []
        hover: list[str] = []

        for m in o_matchups:
            t = m["defender_trophies"]
            wc = m["wins_control"]
            lc = m.get("losses_control", 0)
            ctrl_wr = wc / (wc + lc) if (wc + lc) > 0 else 0.0
            diff = _wr_diff(m)

            xs.append(t)
            ys.append(diff)
            hover.append(
                f"Defender: {m['defender_name']}<br>"
                f"Attacker: {m['officer_name']}<br>"
                f"Trophies: {t:,}<br>"
                f"Ctrl WR: {ctrl_wr:.1%}<br>"
                f"WR Diff: {diff:+.3f}"
            )

        all_x.extend(xs)
        all_y.extend(ys)

        if officer_colors and officer in officer_colors:
            color = officer_colors[officer]
        else:
            color = DATA_COLORS[i % len(DATA_COLORS)]

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                name=officer,
                text=hover,
                hoverinfo="text",
                marker=dict(color=color, opacity=0.8),
                hoverlabel=dict(bgcolor="#1a1a1a", bordercolor="#404040", font=dict(family="JetBrains Mono", color="#ffffff")),
            )
        )

    if len(all_x) >= 3:
        x_arr = np.array(all_x, dtype=float)
        y_arr = np.array(all_y, dtype=float)
        coeffs = np.polyfit(x_arr, y_arr, 1)
        x_line = np.linspace(x_arr.min(), x_arr.max(), 100)
        y_line = np.polyval(coeffs, x_line)

        fig.add_trace(
            go.Scatter(
                x=x_line.tolist(),
                y=y_line.tolist(),
                mode="lines",
                name="Trend (OLS)",
                line=dict(color="#808080", dash="dash"),
                hoverinfo="skip",
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="#404040", line_width=2)

    fig.update_layout(**CHART_LAYOUT)
    fig.update_layout(
        title=dict(text="ricky effect by defender strength", x=0.5, xanchor="center"),
        xaxis_title="defender trophies",
        yaxis_title="wr diff (ricky - control)",
    )

    return pio.to_json(fig)
