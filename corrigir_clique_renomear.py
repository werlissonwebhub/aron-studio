# Corrige o clique no nome do projeto (troca DOMContentLoaded por execucao imediata com retry)
import re, subprocess, os, sys

path = "front/chat.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

if "function setupRename()" in content:
    print("Ja aplicado - nada feito")
    sys.exit(0)

eol = "\r\n" if "\r\n" in content else "\n"

alvo2 = ("            document.addEventListener('DOMContentLoaded', () => {" + eol +
         "                const el = document.getElementById('topbar-project-name');" + eol +
         "                if (el) {")

if content.count(alvo2) != 1:
    print("FALHOU: ancora nao encontrada (", content.count(alvo2), ")")
    sys.exit(1)

subst2 = ("            (function setupRename() {" + eol +
          "                const el = document.getElementById('topbar-project-name');" + eol +
          "                if (!el) { setTimeout(setupRename, 300); return; }" + eol +
          "                {")

content = content.replace(alvo2, subst2, 1)

fecho_antigo = "                    });" + eol + "                }" + eol + "            });"
fecho_novo = "                    });" + eol + "                }" + eol + "            })();"

if content.count(fecho_antigo) < 1:
    print("FALHOU: fechamento nao encontrado")
    sys.exit(1)

content = content.replace(fecho_antigo, fecho_novo, 1)

scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", content, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "vr%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False
        print("JS ERRO bloco", i, ":", r.stderr[:200])
    try: os.remove(t)
    except: pass

if ok:
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
    print("OK - clique corrigido! F5 e clique no nome do projeto")
else:
    print("JS INVALIDO - nao salvo")
    sys.exit(1)
