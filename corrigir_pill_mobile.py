# A pill do editor manual nao sumia no MOBILE.
#
# CAUSA: no desktop a pill fica em top:14px e o transform translateY(-80px) a
# joga para fora da tela. No mobile o CSS muda para bottom:14px — e o mesmo
# translateY(-80px) a move para CIMA, ou seja, para DENTRO da tela. Ela nunca
# sumia. O editor desligava (enabled=false) mas a pill continuava flutuando,
# e por isso parecia que os botoes "nao funcionavam".
#
# CORRECAO: no mobile o transform passa a descer (translateY(140px)) e o
# disable() esconde a pill de verdade com display:none.
#
# IMPORTANTE: depois de rodar, incremente a versao no chat.html:
#   manual-editor.js?v=2  ->  manual-editor.js?v=3
# senao o navegador usa a versao em cache.
import shutil, os
if os.path.exists("front/manual-editor.js"):
    shutil.copy("front/manual-editor.js", "front/manual-editor.js.bak2")
    print("backup: front/manual-editor.js.bak2")
    print()

import subprocess, os, sys

path = "front/manual-editor.js"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in c else "\n"
feitas = []

# ---- FIX 1: CSS mobile - a pill fica em bottom, entao precisa descer para sumir ----
old_css = '".ame-pill{top:auto;bottom:14px;padding:6px 8px 6px 12px}",'
new_css = ('".ame-pill{top:auto;bottom:14px;padding:6px 8px 6px 12px;'
           'transform:translateX(-50%) translateY(140px)}",' + eol +
           '      ".ame-pill.show{transform:translateX(-50%) translateY(0)}",' + eol +
           '      ".ame-pill.ame-hidden{display:none !important}",')

if c.count(old_css) == 1:
    c = c.replace(old_css, new_css, 1)
    feitas.append("CSS mobile: pill agora desce para sumir (antes subia para dentro da tela)")
else:
    print("FALHOU css mobile"); sys.exit(1)

# ---- FIX 2: disable() esconde a pill de verdade ----
old_d = """    clearL();
    if ($('ame-pill')) $('ame-pill').classList.remove('show');
    if ($('ame-panel')) $('ame-panel').classList.remove('open');
    enabled = false;
  }""".replace("\n", eol)

new_d = """    clearL();
    var _pill = $('ame-pill');
    if (_pill) {
      _pill.classList.remove('show');
      // Esconder de verdade: no mobile a pill fica ancorada embaixo e a
      // animacao de transform sozinha nao a tirava da tela.
      _pill.classList.add('ame-hidden');
    }
    if ($('ame-panel')) $('ame-panel').classList.remove('open');
    enabled = false;
  }""".replace("\n", eol)

if c.count(old_d) == 1:
    c = c.replace(old_d, new_d, 1)
    feitas.append("disable(): pill agora e escondida de verdade (display:none)")
else:
    print("FALHOU disable"); sys.exit(1)

# ---- FIX 3: enable() precisa remover o ame-hidden ao reabrir ----
old_e = "    $('ame-pill').classList.add('show');"
new_e = ("    $('ame-pill').classList.remove('ame-hidden');" + eol +
         "    $('ame-pill').classList.add('show');")

if c.count(old_e) == 1:
    c = c.replace(old_e, new_e, 1)
    feitas.append("enable(): pill volta a aparecer ao reabrir o editor")
else:
    print("AVISO: nao achei o ponto do enable (pill pode nao reabrir)")

# validar
open("/tmp/vp.js", "w", encoding="utf-8").write(c)
r = subprocess.run(["node", "--check", "/tmp/vp.js"], capture_output=True, text=True)
os.remove("/tmp/vp.js")
if r.returncode != 0:
    print("JS INVALIDO:", r.stderr[:200]); sys.exit(1)

with open(path, "wb") as f:
    f.write(c.encode("utf-8"))

print("CORRIGIDO:")
for f2 in feitas:
    print("  +", f2)
print()
print("Sintaxe JS: valida")
