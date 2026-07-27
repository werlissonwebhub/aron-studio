# -*- coding: utf-8 -*-
"""
SEO completo da Aron Studio (dominio: aronstudio.com.br)

O que faz:
  index.html  -> title/description otimizados, Open Graph, Twitter Card,
                 canonical, JSON-LD (SoftwareApplication + FAQ), robots index
  chat.html   -> noindex (area logada nao deve ser indexada pelo Google)
  Corrige a og:image quebrada (apontava para img/hero.png, que nao existe)
  Troca todas as URLs de aronelitev1.com.br -> aronstudio.com.br
"""
import re, os, sys, shutil

DOMINIO = "https://aronstudio.com.br"

def backup(p):
    if os.path.exists(p):
        shutil.copy(p, p + ".seobak")

# ---------------------------------------------------------------- INDEX
path = "front/index.html"
if not os.path.exists(path):
    print("FALHOU: front/index.html nao encontrado"); sys.exit(1)

backup(path)
with open(path, "rb") as f:
    h = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in h else "\n"

# 1. Trocar dominio antigo
n_dom = h.count("aronelitev1.com.br")
h = h.replace("https://aronelitev1.com.br", DOMINIO)
h = h.replace("aronelitev1.com.br", "aronstudio.com.br")

# 2. Corrigir og:image quebrada (hero.png nao existe)
h = h.replace('content="https://aronstudio.com.br/img/hero.png"',
              'content="https://aronstudio.com.br/img/og-image.png"')

# 3. Title otimizado
h = re.sub(r"<title>.*?</title>",
           "<title>Aron Studio — Crie sites e apps com IA em segundos | Gerador de sites com inteligência artificial</title>",
           h, count=1, flags=re.S|re.I)

# 4. Description otimizada
h = re.sub(r'<meta\s+name="description"[^>]*content="[^"]*"',
           '<meta name="description" content="Crie sites e aplicativos profissionais com IA em segundos. Descreva o que você precisa e a Aron gera o código completo, com design premium e pronto para publicar. Alternativa brasileira ao Lovable e v0.dev."',
           h, count=1, flags=re.S|re.I)

# 5. Adicionar o que falta antes do </head>
extras = []
if "rel=\"canonical\"" not in h:
    extras.append(f'    <link rel="canonical" href="{DOMINIO}/">')
if 'name="robots"' not in h:
    extras.append('    <meta name="robots" content="index, follow, max-image-preview:large">')
if 'name="keywords"' not in h:
    extras.append('    <meta name="keywords" content="criar site com IA, gerador de sites, inteligência artificial, criar aplicativo com IA, fazer site com IA, alternativa Lovable, v0.dev português, criar site sem código, no-code Brasil">')
if 'property="og:site_name"' not in h:
    extras.append('    <meta property="og:site_name" content="Aron Studio">')
if 'property="og:image:width"' not in h:
    extras.append('    <meta property="og:image:width" content="1200">')
    extras.append('    <meta property="og:image:height" content="630">')

# JSON-LD (dados estruturados — faz o Google exibir com destaque)
if "application/ld+json" not in h:
    jsonld = '''    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "Aron Studio",
      "url": "https://aronstudio.com.br/",
      "applicationCategory": "DeveloperApplication",
      "operatingSystem": "Web",
      "inLanguage": "pt-BR",
      "description": "Plataforma brasileira de IA generativa que cria sites, aplicativos fullstack, dashboards e jogos a partir de uma descrição em português.",
      "image": "https://aronstudio.com.br/img/og-image.png",
      "offers": [
        {"@type": "Offer", "name": "Starter", "price": "29.90", "priceCurrency": "BRL"},
        {"@type": "Offer", "name": "Pro", "price": "59.90", "priceCurrency": "BRL"},
        {"@type": "Offer", "name": "Ultra", "price": "99.90", "priceCurrency": "BRL"}
      ],
      "featureList": [
        "Geração de sites com IA",
        "Aplicativos fullstack com banco de dados e login",
        "Dashboards e painéis administrativos",
        "Jogos interativos",
        "Deploy com um clique"
      ],
      "creator": {"@type": "Organization", "name": "Codding Web Developers", "url": "https://aronstudio.com.br/"}
    }
    </script>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "Como criar um site com inteligência artificial?",
          "acceptedAnswer": {"@type": "Answer", "text": "Na Aron Studio você descreve o site que quer em português e a IA gera o código completo em segundos, com design profissional, responsivo e pronto para publicar."}
        },
        {
          "@type": "Question",
          "name": "A Aron Studio é uma alternativa ao Lovable e ao v0.dev?",
          "acceptedAnswer": {"@type": "Answer", "text": "Sim. A Aron Studio é uma plataforma brasileira de geração de sites e apps com IA, feita em português, com pagamento em PIX e preços em real."}
        },
        {
          "@type": "Question",
          "name": "Preciso saber programar para usar?",
          "acceptedAnswer": {"@type": "Answer", "text": "Não. Basta descrever o que você precisa. A Aron gera o código, o design e a estrutura completa. Você pode publicar direto ou editar o código se quiser."}
        }
      ]
    }
    </script>'''
    extras.append(jsonld)

if extras:
    bloco = eol.join(extras) + eol
    h = h.replace("</head>", bloco + "</head>", 1)

with open(path, "wb") as f:
    f.write(h.encode("utf-8"))

print("index.html:")
print(f"  - dominio trocado ({n_dom} ocorrencias de aronelitev1)")
print("  - title e description otimizados")
print("  - og:image corrigida (hero.png -> og-image.png)")
print("  - canonical, robots, keywords, og:site_name adicionados")
print("  - JSON-LD (SoftwareApplication + FAQ) adicionado")

# ---------------------------------------------------------------- CHAT
path2 = "front/chat.html"
if os.path.exists(path2):
    backup(path2)
    with open(path2, "rb") as f:
        c = f.read().decode("utf-8")
    eol2 = "\r\n" if "\r\n" in c else "\n"

    c = c.replace("https://aronelitev1.com.br", DOMINIO).replace("aronelitev1.com.br", "aronstudio.com.br")

    if 'name="robots"' not in c:
        tags = [
            '    <meta name="robots" content="noindex, nofollow">',
            '    <meta name="description" content="Área do usuário da Aron Studio — crie sites e apps com IA.">',
        ]
        c = c.replace("</head>", eol2.join(tags) + eol2 + "</head>", 1)
        print()
        print("chat.html:")
        print("  - noindex adicionado (area logada nao deve ser indexada)")
        print("  - dominio corrigido")

    with open(path2, "wb") as f:
        f.write(c.encode("utf-8"))

print()
print("OK — SEO aplicado. Backups: *.seobak")
