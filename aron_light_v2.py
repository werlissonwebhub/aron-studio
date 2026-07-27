"""
aron_light_v2.py — Tema claro editorial com cards PRETOS

Corrige o bug da v1 (eyebrow gigante) e aplica a direcao:
  pagina branca + tipografia preta + cards pretos como assinatura

Reexecutavel. Nao toca em server/ nem na aurora do chat.
"""

import os
import shutil

BASE = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front'

START = '<!-- ARON-LIGHT-FIX-START -->'
END = '<!-- ARON-LIGHT-FIX-END -->'

CSS_BASE = """
:root {
  --ink:      #0A0A0A;
  --ink-2:    #1C1C1E;
  --paper:    #FFFFFF;
  --paper-2:  #F7F7F8;
  --line:     #E6E6E8;
  --line-2:   #D1D1D6;
  --grey:     #6E6E73;
  --grey-2:   #A1A1A6;
}

/* ============================================================
   BUGFIX v1 — o eyebrow do hero e um <h1> e foi inflado.
   Nunca dimensionar h1 globalmente neste projeto.
   ============================================================ */
h1[class*="text-[10px]"],
h1[class*="tracking-[0.6em]"] {
  font-size: 11px !important;
  line-height: 1.4 !important;
  letter-spacing: 0.42em !important;
  font-weight: 700 !important;
  color: var(--grey) !important;
  text-transform: uppercase !important;
}

/* ===== BASE ===== */
body { background: var(--paper) !important; color: var(--ink) !important; }

/* ===== TIPOGRAFIA ===== */
h2, h3, h4, h5, .sc-title, .sc-h3 {
  color: var(--ink) !important;
  letter-spacing: -0.035em !important;
  font-weight: 800 !important;
}
h2, .sc-title {
  font-size: clamp(2rem, 4.6vw, 3.5rem) !important;
  line-height: 1.02 !important;
}
h3, .sc-h3 {
  font-size: clamp(1.5rem, 2.8vw, 2.1rem) !important;
  line-height: 1.08 !important;
}
h5 { font-size: 1.0625rem !important; line-height: 1.3 !important; }

/* Titulo principal do hero (e um <p>, nao um h1) */
p[class*="text-[#8A3FFC]"] {
  color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important;
  background: none !important;
  filter: none !important;
  font-size: clamp(2.6rem, 6vw, 4.75rem) !important;
  line-height: 0.98 !important;
  letter-spacing: -0.045em !important;
  font-weight: 900 !important;
}
p[class*="text-[#8A3FFC]"] span,
span[class*="text-[#34D7DD]"] {
  color: var(--grey) !important;
  -webkit-text-fill-color: var(--grey) !important;
  background: none !important;
}
.sc-grad {
  color: var(--grey) !important;
  -webkit-text-fill-color: var(--grey) !important;
  background: none !important;
}

p, .sc-p, .sc-lead { color: var(--grey) !important; }
.sc-kicker {
  color: var(--grey-2) !important;
  font-weight: 700 !important;
  letter-spacing: 0.2em !important;
  font-size: 11px !important;
}

/* ===== INPUT ===== */
div:has(> #user-prompt),
div:has(> textarea#user-prompt) {
  background: var(--paper) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: 20px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 12px 32px rgba(0,0,0,.06) !important;
  backdrop-filter: none !important;
}
div:has(> #user-prompt):focus-within {
  border-color: var(--ink) !important;
  box-shadow: 0 0 0 3px rgba(0,0,0,.07), 0 12px 32px rgba(0,0,0,.08) !important;
}
textarea, input[type="text"], input[type="email"], input[type="search"], #user-prompt {
  background: transparent !important;
  color: var(--ink) !important;
  border: none !important;
  box-shadow: none !important;
}
textarea:focus, input:focus, #user-prompt:focus { outline: none !important; }
::placeholder { color: var(--grey-2) !important; opacity: 1 !important; }

/* ===== BOTOES ===== */
#send-btn, button[type="submit"], .btn-primary {
  background: var(--ink) !important;
  color: #FFF !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 999px !important;
}
#send-btn:hover, button[type="submit"]:hover, .btn-primary:hover {
  background: var(--ink-2) !important;
}
#send-btn svg, #send-btn i, #send-btn * { color: #FFF !important; }

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: var(--paper-2); }
::-webkit-scrollbar-thumb { background: var(--line-2); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: var(--grey-2); }

/* ===== RESPONSIVO ===== */
@media (max-width: 768px) {
  section { padding-left: 20px !important; padding-right: 20px !important; }
  p[class*="text-[#8A3FFC]"] { font-size: clamp(2rem, 9.5vw, 2.9rem) !important; }
  h2, .sc-title { font-size: clamp(1.7rem, 7.5vw, 2.3rem) !important; }
  h3, .sc-h3 { font-size: clamp(1.3rem, 5.5vw, 1.7rem) !important; }
  body { overflow-x: hidden !important; }
  img, video, iframe { max-width: 100% !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
"""

CSS_INDEX = """
/* ============================================================
   ASSINATURA — cards PRETOS sobre pagina branca
   ============================================================ */
section:has(.feature-card), #showcase-criar { background: var(--paper-2) !important; }

.feature-card,
.sc-block,
.showcase-card {
  background: var(--ink) !important;
  border: 1px solid var(--ink) !important;
  border-radius: 20px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,.10) !important;
  transition: transform .3s cubic-bezier(.16,1,.3,1), box-shadow .3s ease !important;
  overflow: hidden !important;
}
.feature-card:hover,
.sc-block:hover,
.showcase-card:hover {
  transform: translateY(-5px) !important;
  box-shadow: 0 18px 44px rgba(0,0,0,.20) !important;
}

/* Texto dentro dos cards pretos */
.feature-card h5, .sc-block h3, .sc-block .sc-h3, .showcase-card h5,
.feature-card h3, .feature-card h4 {
  color: #FFFFFF !important;
}
.feature-card p, .sc-block p, .sc-block .sc-p, .showcase-card p {
  color: rgba(255,255,255,.68) !important;
}
.sc-block .sc-kicker { color: rgba(255,255,255,.55) !important; }
.sc-feat { color: rgba(255,255,255,.78) !important; }
.sc-dot { background: #FFFFFF !important; }

/* Container de icone dentro do card preto */
.feature-card > div:first-child {
  background: rgba(255,255,255,.08) !important;
  border: 1px solid rgba(255,255,255,.14) !important;
}
.feature-card i, .feature-card svg { color: #FFFFFF !important; }

/* Mockups dentro dos cards pretos */
.sc-block [class*="rounded"][class*="bg-"] { background: rgba(255,255,255,.10) !important; }

/* ===== NAVBAR ===== */
nav, header nav {
  background: rgba(255,255,255,.82) !important;
  backdrop-filter: blur(18px) !important;
  border: 1px solid var(--line) !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.03) !important;
}
.nav-link { color: var(--grey) !important; font-weight: 600 !important; }
.nav-link:hover { color: var(--ink) !important; }

/* ===== RODAPE ===== */
footer { background: var(--ink) !important; border-top: none !important; }
footer, footer p, footer a, footer span { color: rgba(255,255,255,.7) !important; }
footer a:hover { color: #FFFFFF !important; }
footer h4, footer h5, footer strong { color: #FFFFFF !important; }
"""

CSS_CHAT = """
/* ===== CHAT ===== */
#app-sidebar {
  background: var(--paper-2) !important;
  border-right: 1px solid var(--line) !important;
}
#app-sidebar a, #app-sidebar button, #app-sidebar span { color: var(--grey) !important; }
#app-sidebar a:hover, #app-sidebar button:hover {
  color: var(--ink) !important;
  background: rgba(0,0,0,.04) !important;
  border-radius: 10px !important;
}

/* Cards de template (Luxury E-commerce etc) — pretos */
[class*="template"], [class*="suggestion"], [class*="preset-card"] {
  background: var(--ink) !important;
  border: none !important;
  border-radius: 14px !important;
}
[class*="template"] *, [class*="suggestion"] * { color: #FFFFFF !important; }

/* Topbar */
header, .topbar { background: var(--paper) !important; border-bottom: 1px solid var(--line) !important; }

/* Codigo */
#code-panel, pre, code {
  background: var(--paper-2) !important;
  color: var(--ink) !important;
  border-color: var(--line) !important;
}

/* Modais */
[role="dialog"], .modal, [id*="modal"] {
  background: var(--paper) !important;
  border: 1px solid var(--line) !important;
  color: var(--ink) !important;
}

/* A aurora/luz pulsante do chat NAO e alterada aqui. */
"""

FILES = {
    'index.html': CSS_BASE + CSS_INDEX,
    'chat.html': CSS_BASE + CSS_CHAT,
    'checkout.html': CSS_BASE,
}


def process(filename, css):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        return f"{filename}: NAO ENCONTRADO"

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    bak = path + '.bak-light'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)

    block = f"{START}\n<style>\n{css}\n</style>\n{END}\n"

    if START in content and END in content:
        ini = content.find(START)
        fim = content.find(END) + len(END) + 1
        content = content[:ini] + block + content[fim:]
        acao = "atualizado"
    else:
        if '</head>' not in content:
            return f"{filename}: sem </head>"
        content = content.replace('</head>', block + '</head>', 1)
        acao = "injetado"

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"{filename}: {acao}"


print("=" * 50)
print("ARON — tema claro editorial (cards pretos)")
print("=" * 50)
for nome, css in FILES.items():
    print("  " + process(nome, css))
print("=" * 50)
print("Ctrl+Shift+R no navegador.")
print("Desfazer: git checkout front/index.html front/chat.html front/checkout.html")
print("=" * 50)
