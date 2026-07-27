# Corrige os 401 com DEV_MODE=false:
#  1. fetchOrThrow so mandava token em /generate/stream -> agora manda em todas
#  2. /api/auth/sync (o login) nao mandava token -> agora manda
import shutil, os
if os.path.exists("front/chat.html"):
    shutil.copy("front/chat.html", "front/chat.html.bak2")
    print("backup: front/chat.html.bak2")
    print()

import re, subprocess, os, sys

path = "front/chat.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in content else "\n"
feitas = []

# ---- FIX 1: fetchOrThrow deve mandar token em TODAS as rotas ----
old1 = ("                            const headers = { 'Content-Type': 'application/json' };" + eol +
        "                            if (url.includes('/generate/stream') || url.includes('/api/generate')) {" + eol)
new1 = ("                            const headers = { 'Content-Type': 'application/json' };" + eol +
        "                            {" + eol)

if content.count(old1) == 1:
    content = content.replace(old1, new1, 1)
    feitas.append("fetchOrThrow: token em TODAS as rotas (era so /generate)")
else:
    print("FALHOU fix1:", content.count(old1)); sys.exit(1)

# ---- FIX 2: /api/auth/sync deve mandar o token do usuario logado ----
old2 = ("                const response = await fetch(`${API_URL}/api/auth/sync`, {" + eol +
        "                    method: 'POST'," + eol +
        "                    headers: { 'Content-Type': 'application/json' }," + eol +
        "                    body: JSON.stringify(payload)" + eol +
        "                });")

new2 = ("                let _syncToken = null;" + eol +
        "                try { _syncToken = await user.getIdToken(); } catch (e) { console.error('sync: falha ao obter token', e); }" + eol +
        "                const _syncHeaders = { 'Content-Type': 'application/json' };" + eol +
        "                if (_syncToken) _syncHeaders['Authorization'] = 'Bearer ' + _syncToken;" + eol +
        "                const response = await fetch(`${API_URL}/api/auth/sync`, {" + eol +
        "                    method: 'POST'," + eol +
        "                    headers: _syncHeaders," + eol +
        "                    body: JSON.stringify(payload)" + eol +
        "                });")

if content.count(old2) == 1:
    content = content.replace(old2, new2, 1)
    feitas.append("auth/sync: agora envia o token do Firebase")
else:
    print("FALHOU fix2:", content.count(old2)); sys.exit(1)

print("CORRIGIDO:")
for f in feitas:
    print("  +", f)

scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", content, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "/tmp/f4%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; print("JS ERRO", i, r.stderr[:200])
    try: os.remove(t)
    except: pass

if ok:
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
    print()
    print("OK - salvo, JS valido")
else:
    print("NADA SALVO"); sys.exit(1)
