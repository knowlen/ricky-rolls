import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_current_officer, get_db
from app.models import LoginRequest, MatchupRequest, OfficerMetaRequest

router = APIRouter(prefix="/api")


@router.post("/login")
def login(request: Request, body: LoginRequest, db: sqlite3.Connection = Depends(get_db)):
    name = body.name.strip()

    # Find or create officer (case-insensitive via COLLATE NOCASE on column)
    row = db.execute(
        "SELECT id, name FROM officers WHERE name = ?", (name,)
    ).fetchone()

    if row:
        officer_id = row["id"]
        officer_name = row["name"]
    else:
        cursor = db.execute(
            "INSERT INTO officers (name) VALUES (?)", (name,)
        )
        officer_id = cursor.lastrowid
        officer_name = name

    request.session["officer_id"] = officer_id
    request.session["officer_name"] = officer_name

    return {"redirect": "/enter"}


@router.post("/matchup")
def upsert_matchup(
    request: Request,
    body: MatchupRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    officer = get_current_officer(request)
    if not officer:
        raise HTTPException(status_code=401, detail="Not logged in")

    cursor = db.execute(
        """
        INSERT INTO matchups (officer_id, defender_id, wins_control, wins_ricky, losses_control, losses_ricky, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(officer_id, defender_id) DO UPDATE SET
            wins_control = COALESCE(excluded.wins_control, matchups.wins_control),
            wins_ricky = COALESCE(excluded.wins_ricky, matchups.wins_ricky),
            losses_control = COALESCE(excluded.losses_control, matchups.losses_control),
            losses_ricky = COALESCE(excluded.losses_ricky, matchups.losses_ricky),
            notes = COALESCE(excluded.notes, matchups.notes),
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            officer["id"],
            body.defender_id,
            body.wins_control,
            body.wins_ricky,
            body.losses_control,
            body.losses_ricky,
            body.notes,
        ),
    )

    # Fetch the updated_at timestamp
    row = db.execute(
        "SELECT updated_at FROM matchups WHERE officer_id = ? AND defender_id = ?",
        (officer["id"], body.defender_id),
    ).fetchone()

    return {"success": True, "updated_at": row["updated_at"] if row else None}


@router.post("/officer/meta")
def update_officer_meta(
    request: Request,
    body: OfficerMetaRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    officer = get_current_officer(request)
    if not officer:
        raise HTTPException(status_code=401, detail="Not logged in")

    db.execute(
        "UPDATE officers SET comp = ?, ricky_replaces = ? WHERE id = ?",
        (body.comp, body.ricky_replaces, officer["id"]),
    )

    return {"success": True}


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=302)


@router.get("/defenders")
def list_defenders(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT id, name, code, comp, trophies FROM defenders ORDER BY name"
    ).fetchall()
    return [dict(row) for row in rows]
