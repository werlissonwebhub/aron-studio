import time
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request
from config import DB_NAME
from models import ChatInitRequest
from security import verify_firebase_token, DEV_MODE

router = APIRouter()

@router.post("/chat/init")
async def chat_init(request: ChatInitRequest, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != request.user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    try:
        chat_id = f"chat_{int(time.time())}"
        title = request.first_prompt[:50] + "..."
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO chats (id, user_id, title, mode, created_at) VALUES (?, ?, ?, ?, datetime('now'))", (chat_id, request.user_id, title, request.mode))
            await db.commit()
        return {"chat_id": chat_id, "title": title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/projects")
async def list_projects(user_id: str, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, title, mode, created_at, thumbnail FROM chats WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{"id": r[0], "title": r[1], "mode": r[2], "created_at": r[3], "thumbnail": r[4]} for r in rows]

@router.get("/api/projects/{chat_id}")
async def get_project(chat_id: str, user_id: str, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, title, full_code, mode, created_at FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")
            full_code_str = row[2]
            response_data = {"id": row[0], "name": row[1], "mode": row[3], "created_at": row[4]}
            if full_code_str and full_code_str.strip().startswith("{") and full_code_str.strip().endswith("}"):
                response_data["full_json"] = full_code_str
                response_data["html_code"] = ""
                response_data["full_code"] = ""
            else:
                response_data["html_code"] = full_code_str
                response_data["full_code"] = full_code_str
            return response_data

@router.delete("/api/projects/{chat_id}")
async def delete_project(chat_id: str, user_id: str, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))
        await db.commit()
    return {"status": "deleted"}

@router.post("/api/save-project")
async def save_project(request: Request, verified_uid: str = Depends(verify_firebase_token)):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        if not DEV_MODE and verified_uid != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado")
        chat_id = data.get("id") or data.get("chat_id")
        full_code = data.get("html_code") or data.get("full_code")
        full_json = data.get("full_json")
        thumbnail = data.get("thumbnail")
        if not full_json and not full_code:
            return {"status": "ignored", "message": "Codigo vazio, nada a salvar"}
        async with aiosqlite.connect(DB_NAME) as db:
            name = data.get("name")
            if not name:
                async with db.execute("SELECT title FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id)) as cursor:
                    row = await cursor.fetchone()
                    name = row[0] if row else "Projeto Sem Nome"
            code_to_save = full_json if full_json else full_code
            await db.execute("UPDATE chats SET full_code = ?, title = ?, thumbnail = COALESCE(?, thumbnail), updated_at = datetime('now') WHERE id = ? AND user_id = ?", (code_to_save, name, thumbnail, chat_id, user_id))
            await db.commit()
        return {"status": "success", "message": "Projeto salvo com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        print(f">>> [ERROR] save_project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/rename-project")
async def rename_project(request: Request, verified_uid: str = Depends(verify_firebase_token)):
    try:
        data = await request.json()
        chat_id = data.get("chat_id")
        user_id = data.get("user_id")
        name = (data.get("name") or "Projeto Sem Nome").strip()[:60]
        if not DEV_MODE and verified_uid != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado")
        if not chat_id or not user_id:
            raise HTTPException(status_code=400, detail="chat_id e user_id obrigatorios")
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE chats SET title = ? WHERE id = ? AND user_id = ?", (name, chat_id, user_id))
            await db.commit()
        return {"status": "success", "name": name}
    except HTTPException:
        raise
    except Exception as e:
        print(f">>> [ERROR] rename_project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
