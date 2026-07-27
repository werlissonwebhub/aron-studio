"""
aron_light_fix.py — Correcao cirurgica do tema claro da Aron Studio

O que faz:
  - Cria backup (.bak-light) de cada arquivo antes de alterar
  - Injeta um bloco CSS de correcao antes de </head>
  - E reexecutavel: se rodar de novo, substitui o bloco em vez de duplicar

O que NAO faz:
  - Nao toca em server/ nem em config.py
  - Nao remove nem reescreve CSS existente
  - Nao mexe na luz pulsante do chat (aurora)
"""

import os
import shutil

BASE = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front'

START = '<!-- ARON-LIGHT-FIX-START -->'
END = '<!-- ARON-LIGHT-FIX-END -->'

# ============================================================
# CSS COMUM — vale para index, chat e checkout
# ============================================================
CSS_BASE = """
/* ===== ESCALA NEUTRA ===== */
:root {
  --a-bg:        #FFFFFF;
  --a-bg-alt:    #FAFAFA;
  --a-surface:   #F4F4F5;
  --a-border:    #E4E4E7;
  --a-border-2:  #D4D4D8;
  --a-muted:     #A1A1AA;
  --a-text-2:    #71717A;
  --a-text-1:    #52525B;
  --a-ink:       #0A0A0A;
}

/* ===== TIPOGRAFIA AGRESSIVA ===== */
h1, h2, h3, .sc-title, .sc-h3 {
  letter-spacing: -0.035em !important;
  line-height: 0.98 !important;
  font-weight: 900 !important;
  color: var(--a-ink) !important;
}
h1 { font-size: clamp(2.4rem, 6.5vw, 5rem) !important; }
h2, .sc-title { font-size: clamp(2rem, 5vw, 3.75rem) !important; }
h3, .sc-h3 { font-size: clamp(1.5rem, 3vw, 2.25rem) !important; }

/* Eyebrows / kickers */
.sc-kicker, [class*="tracking-[0.6em]"], [class*="tracking-[0.3em]"] {
  color: var(--a-text-2) !important;
  font-weight: 700 !important;
  letter-spacing: 0.22em !important;
}

/* Paragrafos */
p, .sc-p, .sc-lead { color: var(--a-text-1) !important; }

/* ===== HERO — titulo legivel ===== */
p[class*="text-[#8A3FFC]"] {
  color: var(--a-ink) !important;
  background: none !important;
  -webkit-text-fill-color: var(--a-ink) !important;
  filter: none !important;
}
p[class*="text-[#8A3FFC]"] span,
span[class*="text-[#34D7DD]"] {
  color: var(--a-text-1) !important;
  background: none !important;
  -webkit-text-fill-color: var(--a-text-1) !important;
  filter: none !important;
}
.sc-grad {
  color: var(--a-text-1) !important;
  background: none !important;
  -webkit-text-fill-color: var(--a-text-1) !important;
}

/* ===== INPUT / TEXTAREA ===== */
textarea,
input[type="text"],
input[type="email"],
input[type="search"],
#user-prompt {
  background: var(--a-bg) !important;
  color: var(--a-ink) !important;
  border: 1px solid var(--a-border) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
}
textarea:focus,
input[type="text"]:focus,
input[type="email"]:focus,
#user-prompt:focus {
  outline: none !important;
  border-color: var(--a-ink) !important;
  box-shadow: 0 0 0 3px rgba(0,0,0,0.06) !important;
}
::placeholder { color: var(--a-muted) !important; opacity: 1 !important; }

/* Caixa que envolve o campo de prompt */
div:has(> #user-prompt),
div:has(> textarea#user-prompt) {
  background: var(--a-bg) !important;
  border: 1px solid var(--a-border) !important;
  border-radius: 18px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 10px 30px rgba(0,0,0,0.05) !important;
}
div:has(> #user-prompt) textarea,
div:has(> #user-prompt) #user-prompt {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

/* ===== BOTOES ===== */
button:not([class*="carousel"]):not(.faq-question),
.btn-action,
a[class*="rounded-full"][class*="bg-"] {
  border-radius: 999px;
}
#send-btn,
button[type="submit"],
.btn-primary {
  background: var(--a-ink) !important;
  color: #FFFFFF !important;
  border: none !important;
  box-shadow: none !important;
}
#send-btn:hover,
button[type="submit"]:hover,
.btn-primary:hover {
  background: #262626 !important;
}
#send-btn svg, #send-btn i { color: #FFFFFF !important; }

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--a-surface); }
::-webkit-scrollbar-thumb { background: var(--a-border-2); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: var(--a-text-2); }

/* ===== RESPONSIVO ===== */
@media (max-width: 768px) {
  section { padding-left: 20px !important; padding-right: 20px !important; }
  h1 { font-size: clamp(2rem, 9vw, 2.75rem) !important; }
  h2, .sc-title { font-size: clamp(1.6rem, 7vw, 2.25rem) !important; }
  h3, .sc-h3 { font-size: clamp(1.25rem, 5.5vw, 1.6rem) !important; }
  .grid { gap: 16px !important; }
  body { overflow-x: hidden !important; }
  img, video, iframe { max-width: 100% !important; height: auto !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
"""

# ============================================================
# CSS EXTRA — so no index.html (cards, secoes, mockups)
# ============================================================
CSS_INDEX = """
/* ===== SECOES ALTERNADAS (da vida aos cards) ===== */
body { background: var(--a-bg) !important; }
section:has(.feature-card),
#showcase-criar {
  background: var(--a-bg-alt) !important;
}

/* ===== CARDS ===== */
.feature-card,
.sc-block,
.showcase-card {
  background: var(--a-bg) !important;
  border: 1px solid var(--a-border) !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
  transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease !important;
}
.feature-card:hover,
.sc-block:hover,
.showcase-card:hover {
  border-color: var(--a-border-2) !important;
  box-shadow: 0 6px 20px rgba(0,0,0,0.07) !important;
  transform: translateY(-3px) !important;
}
.feature-card h5, .showcase-card h5 { color: var(--a-ink) !important; }

/* Containers de icone dentro dos cards */
.feature-card > div:first-child,
[class*="rounded-xl"][class*="bg-cyan-500/10"],
[class*="rounded-xl"][class*="/10"] {
  background: var(--a-surface) !important;
  border: 1px solid var(--a-border) !important;
}
.feature-card i, .feature-card svg { color: var(--a-ink) !important; }

/* Pontinhos de feature */
.sc-dot { background: var(--a-ink) !important; }

/* ===== NAVBAR ===== */
nav, header nav {
  background: rgba(255,255,255,0.85) !important;
  backdrop-filter: blur(16px) !important;
  border-bottom: 1px solid var(--a-border) !important;
  box-shadow: none !important;
}
.nav-link { color: var(--a-text-1) !important; }
.nav-link:hover { color: var(--a-ink) !important; }

/* ===== MOCKUPS ===== */
[class*="rounded"][class*="bg-white/"],
[class*="bg-surface-800"] {
  background: var(--a-surface) !important;
}
</style>
<style>
/* ===== RODAPE ===== */
footer { background: var(--a-bg-alt) !important; border-top: 1px solid var(--a-border) !important; }
footer a { color: var(--a-text-1) !important; }
footer a:hover { color: var(--a-ink) !important; }
"""

# ============================================================
# CSS EXTRA — so no chat.html (NAO toca na aurora)
# ============================================================
CSS_CHAT = """
/* ===== CHAT — sidebar e paineis ===== */
#app-sidebar {
  background: var(--a-bg-alt) !important;
  border-right: 1px solid var(--a-border) !important;
}
#app-sidebar a, #app-sidebar button { color: var(--a-text-1) !important; }
#app-sidebar a:hover, #app-sidebar button:hover {
  color: var(--a-ink) !important;
  background: var(--a-surface) !important;
}

/* Balao de mensagem */
[class*="message"], .chat-bubble {
  border: 1px solid var(--a-border) !important;
  background: var(--a-bg) !important;
  color: var(--a-ink) !important;
}

/* Painel de codigo */
#code-panel, pre, code {
  background: var(--a-surface) !important;
  color: var(--a-ink) !important;
  border-color: var(--a-border) !important;
}

/* Modais */
[role="dialog"], .modal, [id*="modal"] {
  background: var(--a-bg) !important;
  border: 1px solid var(--a-border) !important;
  color: var(--a-ink) !important;
}

/* IMPORTANTE: a luz pulsante do fundo do chat (aurora) NAO e alterada aqui.
   Nenhuma regra acima seleciona #aurora-bg, .aurora, nem o wrapper de preview. */
"""

FILES = {
    'index.html': CSS_BASE + CSS_INDEX,
    'chat.html': CSS_BASE + CSS_CHAT,
    'checkout.html': CSS_BASE,
}


def process(filename, css):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        return f"{filename}: NAO ENCONTRADO — pulado"

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # backup so na primeira vez
    bak = path + '.bak-light'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        bak_msg = "backup criado"
    else:
        bak_msg = "backup ja existia"

    block = f"{START}\n<style>\n{css}\n</style>\n{END}\n"

    # se ja foi injetado antes, substitui
    if START in content and END in content:
        ini = content.find(START)
        fim = content.find(END) + len(END) + 1
        content = content[:ini] + block + content[fim:]
        acao = "bloco atualizado"
    else:
        if '</head>' not in content:
            return f"{filename}: sem </head> — pulado"
        content = content.replace('</head>', block + '</head>', 1)
        acao = "bloco injetado"

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    return f"{filename}: {acao} ({bak_msg})"


print("=" * 52)
print("ARON — correcao do tema claro")
print("=" * 52)
for nome, css in FILES.items():
    print("  " + process(nome, css))
print("=" * 52)
print("Pronto. Abra o site e de Ctrl+Shift+R.")
print()
print("Para desfazer tudo:")
print('  git checkout front/index.html front/chat.html front/checkout.html')
print("=" * 52)
