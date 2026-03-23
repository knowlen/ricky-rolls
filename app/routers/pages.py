import sqlite3
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.dependencies import get_current_officer, get_db
from app.services.charts import (
    DATA_COLORS,
    build_paired_bar,
    build_trophy_scatter,
    build_wr_boxplot,
    empty_chart_json,
)
from app.services.stats import compute_stats, run_wilcoxon

router = APIRouter()
templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)


@router.get("/")
def login_page(request: Request):
    officer = get_current_officer(request)
    if officer:
        return RedirectResponse(url="/enter", status_code=302)
    return templates.TemplateResponse(
        name="login.html", request=request, context={"officer": None, "nav_page": "login"}
    )


@router.get("/enter")
def enter_page(request: Request, db: sqlite3.Connection = Depends(get_db)):
    officer = get_current_officer(request)
    if not officer:
        return RedirectResponse(url="/", status_code=302)

    # Get full officer record for metadata fields
    officer_row = db.execute(
        "SELECT comp, ricky_replaces FROM officers WHERE id = ?",
        (officer["id"],),
    ).fetchone()
    officer_meta = dict(officer_row) if officer_row else {"comp": "", "ricky_replaces": ""}

    defenders = db.execute(
        "SELECT id, name, code, comp, trophies FROM defenders ORDER BY name"
    ).fetchall()

    matchups = db.execute(
        "SELECT defender_id, wins_control, wins_ricky, losses_control, losses_ricky, notes "
        "FROM matchups WHERE officer_id = ?",
        (officer["id"],),
    ).fetchall()

    matchup_map = {
        row["defender_id"]: dict(row) for row in matchups
    }

    return templates.TemplateResponse(
        name="enter.html",
        request=request,
        context={
            "officer": officer,
            "officer_meta": officer_meta,
            "defenders": [dict(d) for d in defenders],
            "matchup_map": matchup_map,
            "nav_page": "enter",
        },
    )


@router.get("/results")
def results_page(request: Request, db: sqlite3.Connection = Depends(get_db)):
    officer = get_current_officer(request)
    if not officer:
        return RedirectResponse(url="/", status_code=302)

    # Get this officer's matchups with defender names
    officer_matchups = db.execute(
        "SELECT m.id, m.officer_id, m.defender_id, m.wins_control, m.wins_ricky, "
        "m.losses_control, m.losses_ricky, "
        "m.notes, m.updated_at, d.name AS defender_name, "
        "d.trophies AS defender_trophies "
        "FROM matchups m "
        "JOIN defenders d ON d.id = m.defender_id "
        "WHERE m.officer_id = ?",
        (officer["id"],),
    ).fetchall()
    officer_matchups = [dict(row) for row in officer_matchups]
    for m in officer_matchups:
        m["officer_name"] = officer["name"]

    if officer_matchups:
        stats = compute_stats(officer_matchups)
        wilcoxon = run_wilcoxon(officer_matchups)
        paired_bar_json = build_paired_bar(officer_matchups)
        trophy_scatter_json = build_trophy_scatter(officer_matchups)
    else:
        stats = {}
        wilcoxon = {}
        paired_bar_json = empty_chart_json("No matchup data yet")
        trophy_scatter_json = empty_chart_json("No matchup data yet")

    # Count incomplete matchups: started but not 5+ total games on both sides
    n_incomplete = sum(
        1 for m in officer_matchups
        if (m["wins_control"] + m["losses_control"] > 0 or m["wins_ricky"] + m["losses_ricky"] > 0)
        and not (m["wins_control"] + m["losses_control"] >= 5 and m["wins_ricky"] + m["losses_ricky"] >= 5)
    )

    row = db.execute(
        "SELECT MAX(updated_at) AS last_updated FROM matchups WHERE officer_id = ?",
        (officer["id"],),
    ).fetchone()
    last_updated = row["last_updated"] if row else None

    return templates.TemplateResponse(
        name="results.html",
        request=request,
        context={
            "officer": officer,
            "matchups": officer_matchups,
            "stats": stats,
            "wilcoxon": wilcoxon,
            "paired_bar_json": paired_bar_json,
            "trophy_scatter_json": trophy_scatter_json,
            "n_incomplete": n_incomplete,
            "last_updated": last_updated,
            "nav_page": "results",
        },
    )


@router.get("/aggregate")
def aggregate_page(request: Request, db: sqlite3.Connection = Depends(get_db)):
    officer = get_current_officer(request)

    # Query all matchups with officer and defender names
    all_matchups = db.execute(
        "SELECT m.id, m.officer_id, m.defender_id, m.wins_control, m.wins_ricky, "
        "m.losses_control, m.losses_ricky, "
        "m.notes, m.updated_at, "
        "o.name AS officer_name, d.name AS defender_name, "
        "d.trophies AS defender_trophies "
        "FROM matchups m "
        "JOIN officers o ON o.id = m.officer_id "
        "JOIN defenders d ON d.id = m.defender_id"
    ).fetchall()
    all_matchups = [dict(row) for row in all_matchups]

    # Group matchups by officer for per-officer stats
    by_officer = defaultdict(list)
    for m in all_matchups:
        by_officer[m["officer_name"]].append(m)

    per_officer_stats = {}
    per_officer_wilcoxon = {}
    for name, matchups in sorted(by_officer.items()):
        per_officer_stats[name] = compute_stats(matchups)
        per_officer_wilcoxon[name] = run_wilcoxon(matchups)

    # Build officer_colors and officer_meta: consistent color assignment by officer id order
    officer_rows = db.execute(
        "SELECT DISTINCT o.id, o.name, o.comp, o.ricky_replaces, "
        "COUNT(m.id) AS matchup_count "
        "FROM officers o "
        "INNER JOIN matchups m ON m.officer_id = o.id "
        "GROUP BY o.id "
        "ORDER BY o.id"
    ).fetchall()
    officer_colors = {
        row["name"]: DATA_COLORS[i % len(DATA_COLORS)]
        for i, row in enumerate(officer_rows)
    }
    officer_meta = {
        row["name"]: {
            "comp": row["comp"],
            "ricky_replaces": row["ricky_replaces"],
            "matchup_count": row["matchup_count"],
        }
        for row in officer_rows
    }

    # Pooled stats across all matchups
    if all_matchups:
        pooled_stats = compute_stats(all_matchups)
        pooled_wilcoxon = run_wilcoxon(all_matchups)
        boxplot_json = build_wr_boxplot(all_matchups, officer_colors=officer_colors)
        trophy_scatter_json = build_trophy_scatter(all_matchups, officer_colors=officer_colors)
    else:
        pooled_stats = {}
        pooled_wilcoxon = {}
        boxplot_json = empty_chart_json("No matchup data yet")
        trophy_scatter_json = empty_chart_json("No matchup data yet")

    # Count incomplete matchups: started but not 5+ total games on both sides
    n_incomplete = sum(
        1 for m in all_matchups
        if (m["wins_control"] + m["losses_control"] > 0 or m["wins_ricky"] + m["losses_ricky"] > 0)
        and not (m["wins_control"] + m["losses_control"] >= 5 and m["wins_ricky"] + m["losses_ricky"] >= 5)
    )

    row = db.execute("SELECT MAX(updated_at) AS last_updated FROM matchups").fetchone()
    last_updated = row["last_updated"] if row else None

    return templates.TemplateResponse(
        name="aggregate.html",
        request=request,
        context={
            "officer": officer,
            "all_matchups": all_matchups,
            "per_officer_stats": per_officer_stats,
            "per_officer_wilcoxon": per_officer_wilcoxon,
            "pooled_stats": pooled_stats,
            "pooled_wilcoxon": pooled_wilcoxon,
            "boxplot_json": boxplot_json,
            "trophy_scatter_json": trophy_scatter_json,
            "n_incomplete": n_incomplete,
            "officer_colors": officer_colors,
            "officer_meta": officer_meta,
            "last_updated": last_updated,
            "nav_page": "aggregate",
        },
    )


@router.get("/chart/{chart_type}")
def chart_page(
    chart_type: str,
    request: Request,
    all: int = 0,
    db: sqlite3.Connection = Depends(get_db),
):
    valid_types = {"paired-bar", "boxplot", "trophy-scatter"}
    if chart_type not in valid_types:
        raise HTTPException(status_code=404, detail="Unknown chart type")

    officer = get_current_officer(request)

    if all:
        # Aggregate scope
        matchups = db.execute(
            "SELECT m.id, m.officer_id, m.defender_id, m.wins_control, m.wins_ricky, "
            "m.losses_control, m.losses_ricky, "
            "o.name AS officer_name, d.name AS defender_name, "
            "d.trophies AS defender_trophies "
            "FROM matchups m "
            "JOIN officers o ON o.id = m.officer_id "
            "JOIN defenders d ON d.id = m.defender_id"
        ).fetchall()
        matchups = [dict(row) for row in matchups]

        officer_rows = db.execute(
            "SELECT DISTINCT o.id, o.name "
            "FROM officers o "
            "INNER JOIN matchups m ON m.officer_id = o.id "
            "ORDER BY o.id"
        ).fetchall()
        officer_colors = {
            row["name"]: DATA_COLORS[i % len(DATA_COLORS)]
            for i, row in enumerate(officer_rows)
        }

        if chart_type == "boxplot":
            chart_json = build_wr_boxplot(matchups, officer_colors=officer_colors)
        else:
            chart_json = build_trophy_scatter(matchups, officer_colors=officer_colors)
        back_url = "/aggregate"
    else:
        # Per-officer scope
        if not officer:
            return RedirectResponse(url="/", status_code=302)

        matchups = db.execute(
            "SELECT m.id, m.officer_id, m.defender_id, m.wins_control, m.wins_ricky, "
            "m.losses_control, m.losses_ricky, "
            "d.name AS defender_name, d.trophies AS defender_trophies "
            "FROM matchups m "
            "JOIN defenders d ON d.id = m.defender_id "
            "WHERE m.officer_id = ?",
            (officer["id"],),
        ).fetchall()
        matchups = [dict(row) for row in matchups]
        for m in matchups:
            m["officer_name"] = officer["name"]

        if chart_type == "paired-bar":
            chart_json = build_paired_bar(matchups)
        else:
            chart_json = build_trophy_scatter(matchups)
        back_url = "/results"

    return templates.TemplateResponse(
        name="chart.html",
        request=request,
        context={"chart_json": chart_json, "back_url": back_url},
    )


@router.get("/admin")
def admin_page(request: Request, db: sqlite3.Connection = Depends(get_db)):
    officer = get_current_officer(request)

    # First visit: require ?key=<ADMIN_KEY>
    if not request.session.get("is_admin"):
        key = request.query_params.get("key")
        if key != settings.ADMIN_KEY:
            return RedirectResponse(url="/", status_code=302)
        request.session["is_admin"] = True

    officers = db.execute(
        "SELECT o.id, o.name, o.comp, o.ricky_replaces, COUNT(m.id) as matchup_count "
        "FROM officers o "
        "LEFT JOIN matchups m ON m.officer_id = o.id "
        "GROUP BY o.id "
        "ORDER BY o.name"
    ).fetchall()
    officers = [dict(o) for o in officers]

    defenders = db.execute(
        "SELECT id, name, code, comp, trophies, created_at FROM defenders ORDER BY name"
    ).fetchall()
    defenders = [dict(d) for d in defenders]

    matchups = db.execute(
        "SELECT m.id, m.officer_id, m.defender_id, m.wins_control, m.wins_ricky, "
        "m.losses_control, m.losses_ricky, "
        "m.notes, m.updated_at, "
        "o.name AS officer_name, d.name AS defender_name "
        "FROM matchups m "
        "JOIN officers o ON o.id = m.officer_id "
        "JOIN defenders d ON d.id = m.defender_id "
        "ORDER BY o.name, d.name"
    ).fetchall()
    matchups = [dict(row) for row in matchups]

    return templates.TemplateResponse(
        name="admin.html",
        request=request,
        context={
            "officer": officer,
            "officers": officers,
            "defenders": defenders,
            "matchups": matchups,
            "nav_page": "admin",
        },
    )
