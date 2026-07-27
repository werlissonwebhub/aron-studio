# Repagina o lado esquerdo da secao de prospeccao
import re

INDEX = "front/index.html"
with open(INDEX, "rb") as f:
    content = f.read().decode("utf-8")

if "np-eyebrow" in content:
    print("Ja aplicado (np-eyebrow existe) - nada feito")
    raise SystemExit

eol = "\r\n" if "\r\n" in content else "\n"

# Ler os arquivos de HTML e CSS novos (devem estar na mesma pasta)
with open("prospect_html.txt", "rb") as f:
    novo_html = f.read().decode("utf-8").replace("\r\n", "\n")
with open("prospect_css.txt", "rb") as f:
    novo_css = f.read().decode("utf-8").replace("\r\n", "\n")

if eol == "\r\n":
    novo_html = novo_html.replace("\n", "\r\n")
    novo_css = novo_css.replace("\n", "\r\n")

# 1. Substituir o bloco <div class="prospect-text"> ... </div> inteiro
#    Ele vai do <div class="prospect-text"> ate o </div> que fecha, logo antes de <div class="prospect-globe-wrap">
pat = re.compile(r'<div class="prospect-text">.*?</div>\s*(?=<div class="prospect-globe-wrap">)', re.DOTALL)
m = pat.search(content)
if not m:
    print("FALHOU: bloco prospect-text nao encontrado")
    raise SystemExit

content = content[:m.start()] + novo_html.strip() + eol + "            " + content[m.end():]
print("HTML do lado esquerdo substituido")

# 2. Injetar o CSS novo antes do primeiro </style>
sclose = content.find("</style>")
if sclose != -1:
    content = content[:sclose] + novo_css + eol + content[sclose:]
    print("CSS novo injetado")

with open(INDEX, "wb") as f:
    f.write(content.encode("utf-8"))
print("OK - lado esquerdo da prospeccao repaginado! F5 para ver")
