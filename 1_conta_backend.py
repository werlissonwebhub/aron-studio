# 1/2 — BACKEND: /api/user/me passa a retornar plano, nome, email e total de projetos
import shutil, os
if os.path.exists("server/routes/auth.py"):
    shutil.copy("server/routes/auth.py", "server/routes/auth.py.bak")
    print("backup: server/routes/auth.py.bak")

import ast, sys

path = "server/routes/auth.py"
with open(path, "r", encoding="utf-8", newline="") as f:
    c = f.read()

eol = "\r\n" if "\r\n" in c else "\n"

old = '''    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT credits, has_received_welcome_bonus FROM users WHERE id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuario nao encontrado")
            return {
                "credits": row[0],
                "has_received_welcome_bonus": bool(row[1]),
            }'''.replace("\n", eol)

new = '''    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT credits, has_received_welcome_bonus, plan, name, email FROM users WHERE id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuario nao encontrado")

        # Total de projetos do usuario no workspace
        async with db.execute(
            "SELECT COUNT(*) FROM chats WHERE user_id = ?",
            (user_id,),
        ) as c2:
            prow = await c2.fetchone()
            total_projetos = prow[0] if prow else 0

        plano = (row[2] or "free").lower()

        return {
            "credits": row[0],
            "has_received_welcome_bonus": bool(row[1]),
            "plan": plano,
            "name": row[3],
            "email": row[4],
            "projects_count": total_projetos,
        }'''.replace("\n", eol)

if c.count(old) != 1:
    print("FALHOU: bloco nao encontrado (", c.count(old), ")"); sys.exit(1)

c = c.replace(old, new, 1)

try:
    ast.parse(c)
except SyntaxError as e:
    print("ERRO SINTAXE:", e); sys.exit(1)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(c)

print("OK - /api/user/me agora retorna: credits, plan, name, email, projects_count")
