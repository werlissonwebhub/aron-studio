# Torna a funcao abrirModalRenomear global para o clique (linha 2204) conseguir acessa-la
import re, subprocess, os, sys

path = "front/chat.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

if "window.abrirModalRenomear = function" in content:
    print("Ja e global - nada feito")
    sys.exit(0)

# 1. Tornar a funcao global
old_def = "function abrirModalRenomear(currentName) {"
new_def = "window.abrirModalRenomear = function(currentName) {"
if content.count(old_def) != 1:
    print("FALHOU: definicao da funcao nao encontrada (", content.count(old_def), ")")
    sys.exit(1)
content = content.replace(old_def, new_def, 1)

# 2. Trocar a chamada para usar window.
old_call = "await abrirModalRenomear(currentName)"
new_call = "await window.abrirModalRenomear(currentName)"
if content.count(old_call) != 1:
    print("FALHOU: chamada nao encontrada (", content.count(old_call), ")")
    sys.exit(1)
content = content.replace(old_call, new_call, 1)

# Validar JS
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", content, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "gg%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False
        print("JS ERRO bloco", i, ":", r.stderr[:150])
    try: os.remove(t)
    except: pass

if ok:
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
    print("OK - modal agora e global! F5 e clique no nome do projeto")
else:
    print("JS invalido - nao salvo")
    sys.exit(1)
