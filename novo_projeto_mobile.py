# Botao "Novo Projeto" na sidebar (menu hamburguer).
#
# PROBLEMA: no mobile o unico caminho para criar projeto novo estava dentro do
# dropdown do topo, que nao e acessivel la. O usuario ficava preso no projeto
# atual e precisava recarregar a pagina.
#
# AGORA: botao em destaque no topo da sidebar. Ao tocar, cria o projeto novo e
# FECHA o menu automaticamente (senao o usuario ficaria olhando para a sidebar
# aberta sem entender que ja funcionou).
import shutil, os
if os.path.exists("front/chat.html"):
    shutil.copy("front/chat.html", "front/chat.html.npbak")
    print("backup: front/chat.html.npbak")
    print()

import re, subprocess, os, sys

path = "front/chat.html"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in c else "\n"

if "sidebar-novo-projeto" in c:
    print("Ja aplicado"); sys.exit(0)

# ---------- 1. Botao na sidebar, logo antes do <nav> ----------
anchor = '                <nav class="p-3 space-y-0.5 mt-2">'
if c.count(anchor) != 1:
    print("FALHOU: <nav> da sidebar nao encontrado"); sys.exit(1)

botao = (
    '                <!-- Novo Projeto (principal acao da sidebar) -->' + eol +
    '                <div class="px-3 mb-1">' + eol +
    '                    <button type="button" id="sidebar-novo-projeto" onclick="novoProjetoSidebar()"' + eol +
    '                        class="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg' + eol +
    '                               bg-gradient-to-r from-[#8A3FFC] to-[#34D7DD] text-white font-semibold text-sm' + eol +
    '                               hover:opacity-90 active:scale-[0.98] transition-all shadow-lg shadow-[#8A3FFC]/20">' + eol +
    '                        <i data-lucide="plus" class="h-4 w-4 flex-shrink-0"></i>' + eol +
    '                        <span class="sidebar-label transition-opacity duration-300">Novo Projeto</span>' + eol +
    '                    </button>' + eol +
    '                </div>' + eol + eol
)

c = c.replace(anchor, botao + anchor, 1)
print("  + botao 'Novo Projeto' na sidebar")

# ---------- 2. Funcao: cria projeto novo E fecha a sidebar no mobile ----------
anchor_fn = "                window.sendPrompt = sendPrompt;"
if c.count(anchor_fn) != 1:
    print("FALHOU: ancora sendPrompt"); sys.exit(1)

func = (
    '                // Novo projeto a partir da sidebar (funciona no mobile)' + eol +
    '                window.novoProjetoSidebar = function () {' + eol +
    '                    // reaproveita a logica que ja existe' + eol +
    '                    if (typeof window.newProjectFromDropdown === "function") {' + eol +
    '                        window.newProjectFromDropdown();' + eol +
    '                    }' + eol +
    '                    // no mobile, fecha o menu para o usuario ver a tela de boas-vindas' + eol +
    '                    try {' + eol +
    '                        const sb = document.getElementById("app-sidebar");' + eol +
    '                        const aberta = sb && !sb.classList.contains("-translate-x-full");' + eol +
    '                        if (aberta && window.innerWidth < 768 && typeof window.toggleMobileSidebar === "function") {' + eol +
    '                            window.toggleMobileSidebar();' + eol +
    '                        }' + eol +
    '                    } catch (e) { console.error("novoProjetoSidebar:", e); }' + eol +
    '                };' + eol + eol
)

c = c.replace(anchor_fn, func + anchor_fn, 1)
print("  + funcao novoProjetoSidebar() (cria + fecha o menu no mobile)")

# ---------- validar ----------
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", c, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "/tmp/np%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; print("JS ERRO", i, r.stderr[:200])
    try: os.remove(t)
    except: pass

if not ok:
    print("NADA SALVO"); sys.exit(1)

with open(path, "wb") as f:
    f.write(c.encode("utf-8"))

print()
print("OK - Novo Projeto acessivel no mobile")
print("Sintaxe JS: valida")
