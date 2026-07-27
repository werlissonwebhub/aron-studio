# Substitui o prompt() nativo de renomear projeto por um modal customizado da Aron
path = "front/chat.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

if "abrirModalRenomear" in content:
    print("Modal JA existe - nada feito")
    raise SystemExit

eol = "\r\n" if "\r\n" in content else "\n"

# 1. Trocar o prompt nativo pela chamada ao modal
import re
m = re.search(r"const newName = prompt\('Renomear projeto:', currentName\);", content)
if not m:
    print("FALHOU: linha do prompt nao encontrada")
    raise SystemExit
content = content.replace(m.group(0), "const newName = await abrirModalRenomear(currentName);", 1)
print("prompt nativo trocado pelo modal")

# 2. Adicionar a funcao antes de window.sendPrompt
anchor = "                window.sendPrompt = sendPrompt;"
if content.count(anchor) != 1:
    print("FALHOU: ancora sendPrompt nao unica")
    raise SystemExit

func_lines = [
    "                // Modal customizado de renomear projeto (substitui prompt nativo)",
    "                function abrirModalRenomear(currentName) {",
    "                    return new Promise(function(resolve) {",
    "                        var ov = document.createElement('div');",
    "                        ov.id = 'rename-modal-overlay';",
    "                        ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);z-index:99999;display:flex;align-items:center;justify-content:center';",
    "                        var modal = document.createElement('div');",
    "                        modal.style.cssText = 'background:#131316;border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:24px;width:90%;max-width:420px;box-shadow:0 30px 60px -15px rgba(0,0,0,0.7)';",
    "                        modal.innerHTML = '<div style=\"font-family:Space Grotesk,sans-serif;font-size:16px;font-weight:600;color:#fff;margin-bottom:6px\">Renomear projeto</div>'",
    "                            + '<div style=\"font-size:12.5px;color:#a1a1aa;margin-bottom:16px\">Escolha um novo nome para o seu projeto.</div>'",
    "                            + '<input id=\"rename-modal-input\" type=\"text\" style=\"width:100%;padding:11px 14px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.12);border-radius:10px;color:#fff;font-size:14px;outline:none;margin-bottom:18px;box-sizing:border-box\" />'",
    "                            + '<div style=\"display:flex;gap:10px;justify-content:flex-end\">'",
    "                            + '<button id=\"rename-cancel\" style=\"padding:9px 18px;background:transparent;border:1px solid rgba(255,255,255,0.12);color:#d4d4d8;border-radius:9px;font-size:13px;font-weight:500;cursor:pointer\">Cancelar</button>'",
    "                            + '<button id=\"rename-save\" style=\"padding:9px 20px;background:linear-gradient(135deg,#8A3FFC,#34D7DD);border:none;color:#fff;border-radius:9px;font-size:13px;font-weight:600;cursor:pointer\">Salvar</button>'",
    "                            + '</div>';",
    "                        ov.appendChild(modal);",
    "                        document.body.appendChild(ov);",
    "                        var input = document.getElementById('rename-modal-input');",
    "                        input.value = currentName;",
    "                        input.focus(); input.select();",
    "                        function fechar(valor) {",
    "                            if (ov.parentNode) ov.parentNode.removeChild(ov);",
    "                            resolve(valor);",
    "                        }",
    "                        document.getElementById('rename-save').onclick = function(){ fechar(input.value); };",
    "                        document.getElementById('rename-cancel').onclick = function(){ fechar(null); };",
    "                        ov.addEventListener('click', function(e){ if (e.target === ov) fechar(null); });",
    "                        input.addEventListener('keydown', function(e){",
    "                            if (e.key === 'Enter') fechar(input.value);",
    "                            if (e.key === 'Escape') fechar(null);",
    "                        });",
    "                    });",
    "                }",
    "",
]
content = content.replace(anchor, eol.join(func_lines) + eol + anchor, 1)
print("funcao abrirModalRenomear adicionada")

# Validar JS
import subprocess, os, time
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", content, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "mr" + str(i) + ".js"
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False
        print("JS ERRO bloco", i, ":", r.stderr[:150])
    time.sleep(0.12)
    try: os.remove(t)
    except: pass

if ok:
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
    print("OK - modal de renomear aplicado!")
    print("F5 na pagina e clique no nome do projeto para testar")
else:
    print("NADA SALVO - erro JS")
