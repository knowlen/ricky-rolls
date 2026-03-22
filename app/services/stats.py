"""Statistical analysis for Ricky vs Control matchup data."""

from __future__ import annotations

import statistics
from typing import Any, Sequence

from scipy.stats import wilcoxon


def compute_stats(matchups: Sequence[Any]) -> dict[str, int | float]:
    """Compute descriptive statistics from completed matchups.

    A matchup is considered "completed" when at least 5 fights have been
    recorded in each condition (control and ricky).

    Args:
        matchups: Sequence of dict-like objects with ``wins_control``,
            ``wins_ricky``, and optionally ``losses_control``,
            ``losses_ricky`` keys (e.g. sqlite3.Row or plain dicts).

    Returns:
        Dictionary with keys total, completed, wr_control, wr_ricky,
        mean_diff, ricky_better, control_better, tied.
    """
    total = len(matchups)

    completed = []
    for m in matchups:
        wc = m["wins_control"]
        lc = m.get("losses_control", 0)
        wr = m["wins_ricky"]
        lr = m.get("losses_ricky", 0)
        if (wc + lc) >= 5 and (wr + lr) >= 5:
            completed.append(m)

    n = len(completed)
    if n == 0:
        return {
            "total": total,
            "completed": 0,
            "wr_control": 0.0,
            "wr_ricky": 0.0,
            "mean_diff": 0.0,
            "ricky_better": 0,
            "control_better": 0,
            "tied": 0,
        }

    wr_controls = []
    wr_rickys = []
    diffs = []
    ricky_better = 0
    control_better = 0
    tied = 0

    for m in completed:
        wc = m["wins_control"]
        lc = m.get("losses_control", 0)
        wr = m["wins_ricky"]
        lr = m.get("losses_ricky", 0)

        wr_c = wc / (wc + lc) if (wc + lc) > 0 else 0.0
        wr_r = wr / (wr + lr) if (wr + lr) > 0 else 0.0

        wr_controls.append(wr_c)
        wr_rickys.append(wr_r)

        diff = wr_r - wr_c
        diffs.append(diff)

        if wr_r > wr_c:
            ricky_better += 1
        elif wr_c > wr_r:
            control_better += 1
        else:
            tied += 1

    return {
        "total": total,
        "completed": n,
        "wr_control": statistics.mean(wr_controls) * 100,
        "wr_ricky": statistics.mean(wr_rickys) * 100,
        "mean_diff": statistics.mean(diffs),
        "ricky_better": ricky_better,
        "control_better": control_better,
        "tied": tied,
    }


def run_wilcoxon(matchups: Sequence[Any]) -> dict[str, Any]:
    """Run a Wilcoxon signed-rank test on matchup win rate differences.

    Pairs where win rate diff is exactly zero are excluded from the test,
    as required by the Wilcoxon procedure.

    Args:
        matchups: Sequence of dict-like objects with ``wins_control``,
            ``wins_ricky``, and optionally ``losses_control``,
            ``losses_ricky`` keys.

    Returns:
        Dictionary with test results including statistic, p_value,
        significance flag, and human-readable interpretation.
    """
    completed = []
    for m in matchups:
        wc = m["wins_control"]
        lc = m.get("losses_control", 0)
        wr = m["wins_ricky"]
        lr = m.get("losses_ricky", 0)
        if (wc + lc) >= 5 and (wr + lr) >= 5:
            completed.append(m)

    diffs = []
    for m in completed:
        wc = m["wins_control"]
        lc = m.get("losses_control", 0)
        wr = m["wins_ricky"]
        lr = m.get("losses_ricky", 0)

        wr_c = wc / (wc + lc) if (wc + lc) > 0 else 0.0
        wr_r = wr / (wr + lr) if (wr + lr) > 0 else 0.0
        diffs.append(wr_r - wr_c)

    nonzero_diffs = [d for d in diffs if d != 0.0]

    n_pairs = len(diffs)
    n_nonzero = len(nonzero_diffs)

    insufficient: dict[str, Any] = {
        "n_pairs": n_pairs,
        "n_nonzero": n_nonzero,
        "statistic": None,
        "p_value": None,
        "significant": False,
        "interpretation": "Insufficient non-tied pairs for Wilcoxon test",
    }

    if n_nonzero < 2:
        return insufficient

    try:
        result = wilcoxon(nonzero_diffs)
    except ValueError:
        return insufficient

    p_value: float = float(result.pvalue)
    statistic: float = float(result.statistic)
    significant = p_value < 0.05

    if significant:
        mean_diff = statistics.mean(diffs)
        if mean_diff > 0:
            interpretation = "Ricky significantly improves win rate"
        else:
            interpretation = "Ricky significantly hurts win rate"
    else:
        interpretation = "No statistically significant difference detected"

    return {
        "n_pairs": n_pairs,
        "n_nonzero": n_nonzero,
        "statistic": statistic,
        "p_value": p_value,
        "significant": significant,
        "interpretation": interpretation,
    }
