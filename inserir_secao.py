# Insere a secao showcase (estilo Lasy, com simulacoes automaticas) na index.html
INDEX = "front/index.html"
SECAO = "secao_showcase.html"

with open(INDEX, "rb") as f:
    content = f.read().decode("utf-8")

if "showcase-criar" in content:
    print("Secao JA existe - removendo a antiga antes de reinserir...")
    import re
    content = re.sub(r'\s*<!-- =+ SECAO: O QUE VOCE PODE CRIAR.*?FIM SECAO SHOWCASE =+ -->', '', content, flags=re.DOTALL)

with open(SECAO, "rb") as f:
    secao = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in content else "\n"
secao = secao.replace("\r\n", "\n")
if eol == "\r\n":
    secao = secao.replace("\n", "\r\n")

# Inserir entre o fim da hero e a how-section
anchor = '    </section>' + eol + eol + '    <section class="how-section">'
count = content.count(anchor)
print("ancora (fim hero + how-section):", count, "x")

if count == 1:
    replacement = '    </section>' + eol + eol + secao + eol + '    <section class="how-section">'
    content = content.replace(anchor, replacement, 1)
    with open(INDEX, "wb") as f:
        f.write(content.encode("utf-8"))
    print("OK - secao inserida! Recarregue a index (F5)")
else:
    print("FALHOU - ancora nao unica. Me avise para ajustar.")
