# CSS CORROMPIDO no manual-editor.js
#
# A regra .ame-pbtn.exit tinha SUMIDO do arquivo e a do .ame-pbtn.save ficou com
# lixo no lugar do box-shadow:  rgba(99,r(--ame-border)
# Duas linhas de CSS foram fundidas e truncadas em alguma edicao anterior.
#
# Consequencia: sem a regra .exit, o botao Sair ficava com 0x0 pixels — existia
# no DOM mas era impossivel de tocar. Por isso "o botao nao funcionava".
#
# Este script restaura as duas regras.
#
# DEPOIS DE RODAR: incremente a versao no chat.html (v=3 -> v=4)
import shutil, os
if os.path.exists("front/manual-editor.js"):
    shutil.copy("front/manual-editor.js", "front/manual-editor.js.bak3")
    print("backup: front/manual-editor.js.bak3")
    print()

import subprocess, os, sys

path = "front/manual-editor.js"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in c else "\n"

LINHA_BOA_SAVE = '      ".ame-pbtn.save{background:linear-gradient(135deg,var(--ame-indigo),var(--ame-violet));color:#fff;box-shadow:0 4px 14px rgba(99,102,241,.35)}",'
LINHA_BOA_EXIT = '      ".ame-pbtn.exit{background:var(--ame-panel2);color:var(--ame-txt);border:1px solid var(--ame-border)}",'

# Ja esta ok?
if '.ame-pbtn.exit{background:var(--ame-panel2)' in c and 'rgba(99,102,241,.35)' in c:
    print("CSS ja esta integro — nada a fazer")
    sys.exit(0)

# Achar a linha corrompida do .save
linhas = c.split(eol)
idx = None
for i, l in enumerate(linhas):
    if '.ame-pbtn.save{' in l:
        idx = i
        break

if idx is None:
    print("FALHOU: nao achei a linha do .ame-pbtn.save")
    sys.exit(1)

print("linha corrompida encontrada (indice", idx, "):")
print("  ", linhas[idx].strip()[:95])
print()

# Substituir a linha corrompida pelas DUAS linhas corretas
linhas[idx] = LINHA_BOA_SAVE
linhas.insert(idx + 1, LINHA_BOA_EXIT)

c = eol.join(linhas)

# validar
open("/tmp/vc.js", "w", encoding="utf-8").write(c)
r = subprocess.run(["node", "--check", "/tmp/vc.js"], capture_output=True, text=True)
os.remove("/tmp/vc.js")
if r.returncode != 0:
    print("JS INVALIDO:", r.stderr[:200])
    sys.exit(1)

with open(path, "wb") as f:
    f.write(c.encode("utf-8"))

print("RESTAURADO:")
print("  + .ame-pbtn.save  (box-shadow estava corrompido)")
print("  + .ame-pbtn.exit  (a regra inteira tinha sumido -> botao Sair ficava 0x0)")
print()
print("Sintaxe JS: valida")
