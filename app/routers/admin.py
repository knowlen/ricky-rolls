import csv
import io
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.dependencies import get_db, require_admin
from app.models import DefenderRequest

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])

# Export route lives under /api but shares the admin guard,
# so we create a separate router for it and merge at include time.
export_router = APIRouter(prefix="/api", dependencies=[Depends(require_admin)])


@router.post("/defender")
def create_defender(body: DefenderRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        cursor = db.execute(
            "INSERT INTO defenders (name, code, comp, trophies) VALUES (?, ?, ?, ?)",
            (body.name.strip(), body.code, body.comp, body.trophies),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"Defender '{body.name}' already exists"
        )

    row = db.execute(
        "SELECT id, name, code, comp, trophies, created_at FROM defenders WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    return dict(row)


@router.put("/defender/{defender_id}")
def update_defender(
    defender_id: int,
    body: DefenderRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    existing = db.execute(
        "SELECT id FROM defenders WHERE id = ?", (defender_id,)
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Defender not found")

    try:
        db.execute(
            "UPDATE defenders SET name = ?, code = ?, comp = ?, trophies = ? WHERE id = ?",
            (body.name.strip(), body.code, body.comp, body.trophies, defender_id),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"Defender name '{body.name}' already taken"
        )

    row = db.execute(
        "SELECT id, name, code, comp, trophies, created_at FROM defenders WHERE id = ?",
        (defender_id,),
    ).fetchone()

    return dict(row)


@router.delete("/defender/{defender_id}")
def delete_defender(
    defender_id: int,
    db: sqlite3.Connection = Depends(get_db),
):
    existing = db.execute(
        "SELECT id FROM defenders WHERE id = ?", (defender_id,)
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Defender not found")

    db.execute("DELETE FROM defenders WHERE id = ?", (defender_id,))

    return {"success": True}


@router.delete("/attacker/{officer_id}")
def delete_attacker(
    officer_id: int,
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
):
    if officer_id == request.session.get("officer_id"):
        raise HTTPException(status_code=400, detail="cannot delete yourself")

    existing = db.execute(
        "SELECT id FROM officers WHERE id = ?", (officer_id,)
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Attacker not found")

    db.execute("DELETE FROM matchups WHERE officer_id = ?", (officer_id,))
    db.execute("DELETE FROM officers WHERE id = ?", (officer_id,))

    return {"success": True}


@export_router.get("/export/csv")
def export_csv(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT o.name AS officer_name, d.name AS defender_name, "
        "m.wins_control, m.wins_ricky, m.losses_control, m.losses_ricky, "
        "m.notes, m.updated_at "
        "FROM matchups m "
        "JOIN officers o ON o.id = m.officer_id "
        "JOIN defenders d ON d.id = m.defender_id "
        "ORDER BY o.name, d.name"
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "attacker", "defender", "wins_control", "wins_ricky",
        "losses_control", "losses_ricky",
        "notes", "updated_at",
    ])
    for row in rows:
        writer.writerow([
            row["officer_name"],
            row["defender_name"],
            row["wins_control"],
            row["wins_ricky"],
            row["losses_control"],
            row["losses_ricky"],
            row["notes"],
            row["updated_at"],
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=matchups_export.csv"
        },
    )
