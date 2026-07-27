# Editor manual no MOBILE:
#  1. Os botoes Salvar/Sair nao respondiam ao toque (o seletor de elementos do
#     proprio editor engolia o evento antes de chegar neles). Agora escutam
#     touchstart/pointerdown com stopPropagation.
#  2. Salvar agora tambem FECHA o editor (antes so salvava e continuava aberto).
#  3. Botoes com area de toque de 40px (era pequena demais para o dedo).
import shutil, os
if os.path.exists("front/manual-editor.js"):
    shutil.copy("front/manual-editor.js", "front/manual-editor.js.bak")
    print("backup: front/manual-editor.js.bak")
    print()

import subprocess, os, sys

path = "front/manual-editor.js"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in c else "\n"
feitas = []

# ---- FIX 1: botoes respondem a TOQUE (nao so click) ----
old_h = """    $('ame-exit').onclick = function () { disable(); };
    $('ame-save').onclick = function () { save(); };""".replace("\n", eol)

new_h = """    // Botoes da pill: no mobile o 'click' era engolido pelo seletor de elementos.
    // Aqui respondemos a pointerdown/touchstart e bloqueamos a propagacao.
    function bindPillBtn(id, fn) {
      var b = $(id);
      if (!b) return;
      var disparado = false;
      function acionar(e) {
        e.preventDefault();
        e.stopPropagation();
        if (disparado) return;
        disparado = true;
        setTimeout(function () { disparado = false; }, 400);
        fn();
      }
      b.addEventListener('touchstart', acionar, { passive: false, capture: true });
      b.addEventListener('pointerdown', acionar, { capture: true });
      b.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); }, true);
    }

    bindPillBtn('ame-exit', function () { disable(); });
    bindPillBtn('ame-save', function () { save(); });""".replace("\n", eol)

if c.count(old_h) == 1:
    c = c.replace(old_h, new_h, 1)
    feitas.append("botoes Salvar/Sair respondem a toque no mobile")
else:
    print("FALHOU: handlers nao encontrados"); sys.exit(1)

# ---- FIX 2: Salvar tambem FECHA o editor ----
old_s = """    if (typeof window.saveProjectToCloud === 'function') {
      window.saveProjectToCloud(false);
    } else {
      toast('HTML capturado (salvamento na nuvem indisponível)');
    }
  }""".replace("\n", eol)

new_s = """    if (typeof window.saveProjectToCloud === 'function') {
      window.saveProjectToCloud(false);
    } else {
      toast('HTML capturado (salvamento na nuvem indisponível)');
    }

    // Salvar tambem encerra o modo de edicao (o usuario espera isso)
    setTimeout(function () { disable(); }, 350);
  }""".replace("\n", eol)

if c.count(old_s) == 1:
    c = c.replace(old_s, new_s, 1)
    feitas.append("Salvar agora fecha o editor depois de salvar")
else:
    print("FALHOU: funcao save() nao encontrada"); sys.exit(1)

# ---- FIX 3: area de toque maior nos botoes (mobile) ----
old_css = '".ame-pill{top:auto;bottom:14px;padding:6px 8px 6px 12px}",'
new_css = ('".ame-pill{top:auto;bottom:14px;padding:6px 8px 6px 12px}",' + eol +
           '      ".ame-pbtn{min-height:40px;padding:10px 16px;font-size:13px;touch-action:manipulation}",')

if c.count(old_css) == 1:
    c = c.replace(old_css, new_css, 1)
    feitas.append("botoes maiores no mobile (area de toque de 40px)")

# validar
open("/tmp/chk_ed.js", "w", encoding="utf-8").write(c)
r = subprocess.run(["node", "--check", "/tmp/chk_ed.js"], capture_output=True, text=True)
os.remove("/tmp/chk_ed.js")

if r.returncode != 0:
    print("JS INVALIDO:", r.stderr[:250]); sys.exit(1)

with open(path, "wb") as f:
    f.write(c.encode("utf-8"))

print("CORRIGIDO:")
for f2 in feitas:
    print("  +", f2)
print()
print("Sintaxe JS: valida")
