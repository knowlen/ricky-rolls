from fastapi import Request, HTTPException
from starlette.requests import Request as StarletteRequest

from app.database import get_connection


def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_current_officer(request: StarletteRequest) -> dict | None:
    officer_id = request.session.get("officer_id")
    if not officer_id:
        return None
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, name FROM officers WHERE id = ?", (officer_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        request.session.clear()
        return None
    return {"id": row["id"], "name": row["name"]}


def require_admin(request: Request):
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
