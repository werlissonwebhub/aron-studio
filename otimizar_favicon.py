# Otimiza o favicon: 644 KB -> ~10 KB
# Gera: favicon-32.png (aba do navegador) e apple-touch-icon.png (iOS)
import os
try:
    from PIL import Image
except ImportError:
    print("Instale o Pillow: pip install pillow")
    raise SystemExit(1)

src = "front/img/studio-aron.png"
if not os.path.exists(src):
    print("FALHOU: nao achei", src)
    raise SystemExit(1)

orig = os.path.getsize(src)
im = Image.open(src).convert("RGBA")
print(f"original: {im.size[0]}x{im.size[1]} | {orig/1024:.0f} KB")

# 1. Favicon 32x32 (o que aparece na aba)
f32 = im.copy()
f32.thumbnail((32, 32), Image.LANCZOS)
canvas32 = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
canvas32.paste(f32, ((32 - f32.width)//2, (32 - f32.height)//2), f32)
canvas32.save("front/img/favicon-32.png", "PNG", optimize=True)

# 2. Apple touch icon 180x180 (quando salvam na tela do iPhone)
f180 = im.copy()
f180.thumbnail((180, 180), Image.LANCZOS)
canvas180 = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
canvas180.paste(f180, ((180 - f180.width)//2, (180 - f180.height)//2), f180)
canvas180.save("front/img/apple-touch-icon.png", "PNG", optimize=True)

n32 = os.path.getsize("front/img/favicon-32.png")
n180 = os.path.getsize("front/img/apple-touch-icon.png")
print(f"favicon-32.png:       {n32/1024:.1f} KB")
print(f"apple-touch-icon.png: {n180/1024:.1f} KB")
print(f"economia: {(orig - n32)/1024:.0f} KB por carregamento de pagina")
print()

# 3. Atualizar as tags nas duas paginas
for arq in ["front/index.html", "front/chat.html"]:
    if not os.path.exists(arq):
        continue
    with open(arq, "rb") as f:
        h = f.read().decode("utf-8")
    antes = h
    h = h.replace('href="img/studio-aron.png"', 'href="/img/favicon-32.png"')
    h = h.replace('href="/img/studio-aron.png"', 'href="/img/favicon-32.png"')
    # apple-touch usa o 180
    h = h.replace('<link rel="apple-touch-icon" href="/img/favicon-32.png">',
                  '<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">')
    if h != antes:
        with open(arq, "wb") as f:
            f.write(h.encode("utf-8"))
        print("atualizado:", arq)

print()
print("OK - favicon otimizado. Teste em janela anonima (Ctrl+Shift+N).")
