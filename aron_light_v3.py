"""
aron_light_v3.py — Ajustes + diagnostico

Corrige:
  - Input: fundo branco, borda preta, texto e icones pretos
  - Textos cinza claro demais -> cinza escuro com contraste
  - Cards genericos que ficaram sem vida -> tratamento preto

E imprime a estrutura real do HTML do input e dos cards,
para eu conseguir mirar com precisao caso algo nao pegue.
"""

import os
import re
import shutil

BASE = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front'
START = '<!-- ARON-LIGHT-FIX-START -->'
END = '<!-- ARON-LIGHT-FIX-END -->'

CSS_BASE = """
:root {
  --ink:      #0A0A0A;
  --ink-2:    #1C1C1E;
  --paper:    #FFFFFF;
  --paper-2:  #F5F5F7;
  --line:     #DEDEE3;
  --line-2:   #0A0A0A;
  --grey:     #3A3A3C;
  --grey-2:   #636366;
}

/* Eyebrow do hero e um <h1> — nunca inflar */
h1[class*="text-[10px]"], h1[class*="tracking-[0.6em]"] {
  font-size: 11px !important;
  line-height: 1.4 !important;
  letter-spacing: .4em !important;
  font-weight: 700 !important;
  color: var(--grey-2) !important;
  text-transform: uppercase !important;
}

body { background: var(--paper) !important; color: var(--ink) !important; }

/* ===== TIPOGRAFIA — mais contraste ===== */
h2, h3, h4, h5, .sc-title, .sc-h3 {
  color: var(--ink) !important;
  letter-spacing: -.035em !important;
  font-weight: 800 !important;
}
h2, .sc-title { font-size: clamp(2rem, 4.6vw, 3.5rem) !important; line-height: 1.02 !important; }
h3, .sc-h3    { font-size: clamp(1.5rem, 2.8vw, 2.1rem) !important; line-height: 1.08 !important; }
h5            { font-size: 1.0625rem !important; line-height: 1.3 !important; }

p[class*="text-[#8A3FFC]"] {
  color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important;
  background: none !important; filter: none !important;
  font-size: clamp(2.6rem, 6vw, 4.75rem) !important;
  line-height: .98 !important;
  letter-spacing: -.045em !important;
  font-weight: 900 !important;
}
/* Segunda linha do titulo: preto tambem, so muda o peso */
p[class*="text-[#8A3FFC]"] span, span[class*="text-[#34D7DD]"] {
  color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important;
  background: none !important;
  font-weight: 500 !important;
}
.sc-grad {
  color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important;
  background: none !important;
  font-weight: 500 !important;
}

/* Paragrafos com contraste real */
p, .sc-p, .sc-lead { color: var(--grey) !important; }
.sc-kicker {
  color: var(--ink) !important;
  font-weight: 700 !important;
  letter-spacing: .2em !important;
  font-size: 11px !important;
}

/* ============================================================
   INPUT — branco, borda preta, texto e icones pretos
   Varios seletores de fallback para pegar a estrutura real
   ============================================================ */
div:has(> #user-prompt),
div:has(> textarea#user-prompt),
div:has(> div > #user-prompt),
form:has(#user-prompt),
[class*="prompt"]:has(textarea),
[class*="input-wrap"], [class*="input-container"], [class*="chat-input"] {
  background: #FFFFFF !important;
  border: 1.5px solid var(--ink) !important;
  border-radius: 18px !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}
div:has(> #user-prompt):focus-within,
form:has(#user-prompt):focus-within {
  box-shadow: 0 0 0 3px rgba(0,0,0,.10) !important;
}

textarea, input[type="text"], input[type="email"], input[type="search"], #user-prompt {
  background: transparent !important;
  color: var(--ink) !important;
  border: none !important;
  box-shadow: none !important;
  -webkit-text-fill-color: var(--ink) !important;
}
textarea:focus, input:focus, #user-prompt:focus { outline: none !important; }
::placeholder { color: var(--grey-2) !important; opacity: 1 !important; }

/* Icones do input (clipe, microfone, grid) pretos */
div:has(> #user-prompt) i,
div:has(> #user-prompt) svg,
form:has(#user-prompt) i,
form:has(#user-prompt) svg,
#clip-btn, #clip-btn i, #clip-btn svg,
[id*="mic"], [id*="mic"] i, [id*="mic"] svg {
  color: var(--ink) !important;
  stroke: var(--ink) !important;
}
#clip-btn, [id*="mic"] { background: transparent !important; }

/* ===== BOTOES ===== */
#send-btn, button[type="submit"], .btn-primary {
  background: var(--ink) !important;
  color: #FFF !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 999px !important;
}
#send-btn:hover, button[type="submit"]:hover { background: var(--ink-2) !important; }
#send-btn *, button[type="submit"] * { color: #FFF !important; stroke: #FFF !important; }

::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: var(--paper-2); }
::-webkit-scrollbar-thumb { background: #C7C7CC; border-radius: 8px; }

@media (max-width: 768px) {
  section { padding-left: 20px !important; padding-right: 20px !important; }
  p[class*="text-[#8A3FFC]"] { font-size: clamp(2rem, 9.5vw, 2.9rem) !important; }
  h2, .sc-title { font-size: clamp(1.7rem, 7.5vw, 2.3rem) !important; }
  h3, .sc-h3 { font-size: clamp(1.3rem, 5.5vw, 1.7rem) !important; }
  body { overflow-x: hidden !important; }
  img, video, iframe { max-width: 100% !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration:.01ms !important; transition-duration:.01ms !important; }
}
"""

CSS_INDEX = """
/* ============================================================
   CARDS PRETOS — inclui catch-all para grids de cards
   ============================================================ */
section:has(.feature-card), #showcase-criar { background: var(--paper-2) !important; }

.feature-card,
.sc-block,
.showcase-card,
section .grid > div:has(> h5),
section .grid > div:has(> div > h5),
section .grid > div:has(> h3):not(:has(.grid)) {
  background: var(--ink) !important;
  border: 1px solid var(--ink) !important;
  border-radius: 20px !important;
  padding: 28px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,.10) !important;
  transition: transform .3s cubic-bezier(.16,1,.3,1), box-shadow .3s ease !important;
}
.feature-card:hover, .sc-block:hover, .showcase-card:hover,
section .grid > div:has(> h5):hover {
  transform: translateY(-5px) !important;
  box-shadow: 0 18px 44px rgba(0,0,0,.22) !important;
}

/* Texto branco dentro de card preto */
.feature-card h5, .feature-card h3, .feature-card h4,
.sc-block h3, .sc-block .sc-h3, .showcase-card h5,
section .grid > div:has(> h5) h5,
section .grid > div:has(> h5) h3 {
  color: #FFFFFF !important;
}
.feature-card p, .sc-block p, .sc-block .sc-p, .showcase-card p,
section .grid > div:has(> h5) p {
  color: rgba(255,255,255,.72) !important;
}
.sc-block .sc-kicker { color: rgba(255,255,255,.6) !important; }
.sc-feat { color: rgba(255,255,255,.8) !important; }
.sc-dot  { background: #FFFFFF !important; }

/* Icone dentro do card preto */
.feature-card > div:first-child,
section .grid > div:has(> h5) > div:first-child {
  background: rgba(255,255,255,.10) !important;
  border: 1px solid rgba(255,255,255,.16) !important;
}
.feature-card i, .feature-card svg,
section .grid > div:has(> h5) i,
section .grid > div:has(> h5) svg {
  color: #FFFFFF !important; stroke: #FFFFFF !important;
}

.sc-block [class*="rounded"][class*="bg-"] { background: rgba(255,255,255,.10) !important; }

/* ===== NAVBAR ===== */
nav, header nav {
  background: rgba(255,255,255,.85) !important;
  backdrop-filter: blur(18px) !important;
  border: 1px solid var(--line) !important;
}
.nav-link { color: var(--grey) !important; font-weight: 600 !important; }
.nav-link:hover { color: var(--ink) !important; }

/* ===== RODAPE ===== */
footer { background: var(--ink) !important; border-top: none !important; }
footer, footer p, footer a, footer span { color: rgba(255,255,255,.72) !important; }
footer a:hover, footer h4, footer h5, footer strong { color: #FFF !important; }
"""

CSS_CHAT = """
#app-sidebar { background: var(--paper-2) !important; border-right: 1px solid var(--line) !important; }
#app-sidebar a, #app-sidebar button, #app-sidebar span { color: var(--grey) !important; }
#app-sidebar a:hover, #app-sidebar button:hover {
  color: var(--ink) !important; background: rgba(0,0,0,.05) !important; border-radius: 10px !important;
}
[class*="template"], [class*="suggestion"], [class*="preset-card"] {
  background: var(--ink) !important; border: none !important; border-radius: 14px !important;
}
[class*="template"] *, [class*="suggestion"] * { color: #FFFFFF !important; }
header, .topbar { background: var(--paper) !important; border-bottom: 1px solid var(--line) !important; }
#code-panel, pre, code {
  background: var(--paper-2) !important; color: var(--ink) !important; border-color: var(--line) !important;
}
[role="dialog"], .modal, [id*="modal"] {
  background: var(--paper) !important; border: 1px solid var(--line) !important; color: var(--ink) !important;
}
/* A aurora do chat nao e alterada aqui. */
"""

FILES = {
    'index.html': CSS_BASE + CSS_INDEX,
    'chat.html': CSS_BASE + CSS_CHAT,
    'checkout.html': CSS_BASE,
}


def aplicar(filename, css):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        return f"{filename}: NAO ENCONTRADO", None

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    bak = path + '.bak-light'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)

    block = f"{START}\n<style>\n{css}\n</style>\n{END}\n"

    if START in content and END in content:
        i = content.find(START)
        j = content.find(END) + len(END) + 1
        content = content[:i] + block + content[j:]
        acao = "atualizado"
    else:
        if '</head>' not in content:
            return f"{filename}: sem </head>", None
        content = content.replace('</head>', block + '</head>', 1)
        acao = "injetado"

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"{filename}: {acao}", content


def diagnostico(filename, content):
    """Imprime a estrutura real do input e dos cards."""
    if not content:
        return
    print()
    print("-" * 58)
    print(f"DIAGNOSTICO — {filename}")
    print("-" * 58)

    # limpa o bloco injetado para nao poluir
    if START in content:
        i = content.find(START)
        j = content.find(END) + len(END)
        content = content[:i] + content[j:]

    # 1) contexto do #user-prompt
    idx = content.find('id="user-prompt"')
    if idx == -1:
        idx = content.find("id='user-prompt'")
    if idx != -1:
        ini = max(0, idx - 900)
        trecho = content[ini:idx + 300]
        # so as tags de abertura de div, para ver as classes
        tags = re.findall(r'<(?:div|form|textarea)[^>]{0,300}>', trecho)
        print("\n[INPUT] tags que envolvem o #user-prompt:")
        for t in tags[-6:]:
            print("   " + t[:240])
    else:
        print("\n[INPUT] #user-prompt nao encontrado neste arquivo.")

    # 2) classes de containers que parecem card
    print("\n[CARDS] classes de div que contem <h5> ou <h3>:")
    achados = set()
    for m in re.finditer(r'<div class="([^"]{5,200})"', content):
        cls = m.group(1)
        depois = content[m.end():m.end() + 700]
        if '<h5' in depois or '<h3' in depois:
            achados.add(cls.strip()[:150])
    for c in sorted(achados)[:14]:
        print("   ." + c)
    if not achados:
        print("   (nenhum encontrado)")


print("=" * 58)
print("ARON — tema claro v3")
print("=" * 58)
resultados = []
for nome, css in FILES.items():
    msg, conteudo = aplicar(nome, css)
    print("  " + msg)
    resultados.append((nome, conteudo))

for nome, conteudo in resultados:
    if nome in ('index.html', 'chat.html'):
        diagnostico(nome, conteudo)

print()
print("=" * 58)
print("Ctrl+Shift+R no navegador.")
print("Desfazer: git checkout front/")
print("=" * 58)
