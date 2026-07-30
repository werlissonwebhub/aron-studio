import aiosqlite
from datetime import datetime
from fastapi import APIRouter, HTTPException
from config import DB_NAME
from models import FeedbackIn

router = APIRouter()

_CREATE_SQL = "CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, chat_id TEXT, rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL)"


@router.post("/api/feedback")
async def submit_feedback(fb: FeedbackIn):
    if fb.rating < 1 or fb.rating > 5:
        raise HTTPException(status_code=400, detail="rating deve ser entre 1 e 5")
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(_CREATE_SQL)
        await db.execute(
            "INSERT INTO feedback (user_id, chat_id, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (fb.user_id, fb.chat_id, int(fb.rating),
             (fb.comment or "")[:2000], datetime.utcnow().isoformat())
        )
        await db.commit()
    return {"status": "ok"}


@router.get("/api/feedback/list")
async def list_feedback(key: str = ""):
    if key != "TROQUE_ESTA_SENHA":
        raise HTTPException(status_code=403, detail="Acesso negado")
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, user_id, chat_id, rating, comment, created_at "
            "FROM feedback ORDER BY id DESC LIMIT 200"
        )
        rows = await cur.fetchall()
    return {"total": len(rows), "feedback": [dict(r) for r in rows]}
