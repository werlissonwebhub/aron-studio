"""
aron_light_v4.py - Patch mirado nas classes REAIS (revelado pelo diagnostico)
Injeta ANTES de </body> para vencer na cascata.
"""
import os, shutil

BASE = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front'
START = '<!-- ARON-PATCH-START -->'
END = '<!-- ARON-PATCH-END -->'

CSS_INDEX = """
/* ===== INPUT DA LANDING ===== */
[class*="rounded-2xl"]:has(textarea),
[class*="rounded-xl"]:has(textarea),
div:has(> textarea):not(nav):not(header) {
  background: #FFFFFF !important;
  border: 1.5px solid #0A0A0A !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}
textarea { background: transparent !important; color: #0A0A0A !important; -webkit-text-fill-color: #0A0A0A !important; }
textarea::placeholder { color: #636366 !important; opacity: 1 !important; }
div:has(> textarea) i, div:has(> textarea) svg,
div:has(> textarea) button i, div:has(> textarea) button svg { color: #0A0A0A !important; stroke: #0A0A0A !important; }

/* ===== CARDS - vencer o glow-border ===== */
.feature-card.glow-border, .feature-card.glow-border.reveal {
  background: #0A0A0A !important;
  border: 1px solid #0A0A0A !important;
  border-radius: 20px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,.10) !important;
}
.feature-card.glow-border::before, .feature-card.glow-border::after { display: none !important; }
.feature-card.glow-border:hover { transform: translateY(-5px) !important; box-shadow: 0 18px 44px rgba(0,0,0,.22) !important; }
.feature-card.glow-border h5 { color: #FFFFFF !important; }
.feature-card.glow-border p { color: rgba(255,255,255,.72) !important; }

/* Icones coloridos dentro dos cards */
.feature-card .h-12.w-12.rounded-xl,
.feature-card [class*="bg-[#8A3FFC]/10"],
.feature-card [class*="bg-cyan-500/10"] {
  background: rgba(255,255,255,.10) !important;
  border: 1px solid rgba(255,255,255,.16) !important;
}
.feature-card [class*="text-[#34D7DD]"],
.feature-card [class*="text-[#8A3FFC]"],
.feature-card .h-12 i, .feature-card .h-12 svg {
  color: #FFFFFF !important; stroke: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important;
}

/* Cards de build */
.build-block, .build-badge {
  background: #0A0A0A !important; border: 1px solid #0A0A0A !important; border-radius: 18px !important;
}
.build-block h3, .build-block h5 { color: #FFFFFF !important; }
.build-block p { color: rgba(255,255,255,.72) !important; }
"""

CSS_CHAT = """
/* ===== INPUT DO CHAT ===== */
div.w-full.relative:has(#user-prompt),
[class*="bg-[#FAFAFA]"]:has(#user-prompt),
[class*="bg-[#FAFAFA]"][class*="border-[#E4E4E7]"] {
  background: #FFFFFF !important;
  border: 1.5px solid #0A0A0A !important;
  box-shadow: none !important;
}
#user-prompt { background: transparent !important; color: #0A0A0A !important; -webkit-text-fill-color: #0A0A0A !important; }
#dynamic-placeholder { color: #636366 !important; }
div:has(#user-prompt) button i, div:has(#user-prompt) button svg,
#clip-btn i, #clip-btn svg { color: #0A0A0A !important; stroke: #0A0A0A !important; }
"""

FILES = {'index.html': CSS_INDEX, 'chat.html': CSS_CHAT}

def patch(filename, css):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        return f"{filename}: NAO ENCONTRADO"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    bak = path + '.bak-patch'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    block = f"{START}\n<style>\n{css}\n</style>\n{END}\n"
    if START in content and END in content:
        i = content.find(START); j = content.find(END) + len(END) + 1
        content = content[:i] + block + content[j:]; acao = "atualizado"
    elif '</body>' in content:
        content = content.replace('</body>', block + '</body>', 1); acao = "injetado antes de </body>"
    else:
        content = content.replace('</head>', block + '</head>', 1); acao = "injetado no head"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"{filename}: {acao}"

print("=" * 50)
print("ARON - patch v4 (classes reais)")
print("=" * 50)
for nome, css in FILES.items():
    print("  " + patch(nome, css))
print("=" * 50)
print("Ctrl+Shift+R. Desfazer: git checkout front/")
print("=" * 50)
