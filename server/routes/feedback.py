import aiosqlite
from datetime import datetime
from fastapi import APIRouter, HTTPException
from config import DB_NAME
from models import FeedbackIn

router = APIRouter()

import smtplib
import asyncio
from email.mime.text import MIMEText

GMAIL_USER = "werlissoncarvalho9@gmail.com"
GMAIL_APP_PASSWORD = "xyxmuefyckdtjfdw"
EMAIL_DESTINO = "werlissoncarvalho9@gmail.com"


def _enviar_email_sync(rating: int, comment: str):
    try:
        selo = "CURTIU" if rating >= 3 else "NAO CURTIU"
        corpo = (
            "Novo feedback recebido na Aron Studio:\n\n"
            f"Avaliacao: {selo}\n"
            f"Comentario: {comment or '(sem comentario)'}\n"
        )
        msg = MIMEText(corpo, "plain", "utf-8")
        msg["Subject"] = f"[Aron] Feedback: {selo}"
        msg["From"] = GMAIL_USER
        msg["To"] = EMAIL_DESTINO
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, [EMAIL_DESTINO], msg.as_string())
    except Exception as e:
        print("Falha ao enviar email de feedback:", e)


async def _notificar_email(rating: int, comment: str):
    # roda o SMTP (bloqueante) num thread pra nao travar o event loop
    await asyncio.to_thread(_enviar_email_sync, rating, comment)


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
    # envia o e-mail em background (nao bloqueia a resposta)
    asyncio.create_task(_notificar_email(int(fb.rating), fb.comment or ""))
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
