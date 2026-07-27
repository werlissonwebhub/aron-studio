path = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove o CSS anterior (luz dentro do card)
start_marker = '<style>\n/* ===== Titulo metalico roxo + azul bebe (cores da logo Aron) ===== */'
end_marker = '</style>\n</head>'

si = content.find(start_marker)
ei = content.find(end_marker)

new_css = '''<style>
/* ===== Titulo metalico roxo + azul bebe (cores da logo Aron) ===== */
.aron-metallic-title {
    background: linear-gradient(180deg, #a5c8ff 0%, #6d7fd6 22%, #3d2f8f 46%, #b8d4ff 60%, #2a1f6b 80%, #8fa8f0 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; color: transparent;
    filter: drop-shadow(0 2px 12px rgba(109,127,214,0.4));
    background-size: 100% 200%;
    animation: aronMetallicShine 6s ease-in-out infinite;
}
.aron-metallic-title span {
    background: linear-gradient(180deg, #bfe0ff 0%, #7ba8e8 28%, #4a3f9e 52%, #cfe6ff 66%, #5a4fb0 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; color: transparent;
}
@keyframes aronMetallicShine {
    0%, 100% { background-position: 0% 0%; }
    50% { background-position: 0% 100%; }
}

/* ===== Luz brilhante ATRAS e AO REDOR dos cards grandes (estilo huly) ===== */
#showcase-criar .sc-block {
    position: relative;
    overflow: visible;
}
/* Halo de luz que vaza pelas bordas externas do card */
#showcase-criar .sc-block::before {
    content: "";
    position: absolute;
    inset: -40px;
    border-radius: 32px;
    background:
        radial-gradient(ellipse 70% 50% at 50% 0%, rgba(52,215,221,0.30) 0%, transparent 65%),
        radial-gradient(ellipse 60% 60% at 15% 50%, rgba(138,63,252,0.28) 0%, transparent 70%),
        radial-gradient(ellipse 60% 60% at 85% 50%, rgba(109,127,214,0.26) 0%, transparent 70%),
        radial-gradient(ellipse 70% 45% at 50% 100%, rgba(191,224,255,0.20) 0%, transparent 65%);
    filter: blur(38px);
    opacity: 0.75;
    z-index: -1;
    pointer-events: none;
    animation: aronGlowBreath 5s ease-in-out infinite;
}
@keyframes aronGlowBreath {
    0%, 100% { opacity: 0.55; transform: scale(1); }
    50%      { opacity: 0.95; transform: scale(1.03); }
}
/* Delays diferentes por card */
#showcase-criar .sc-block:nth-of-type(2)::before { animation-delay: 1.6s; }
#showcase-criar .sc-block:nth-of-type(3)::before { animation-delay: 3.2s; }
#showcase-criar .sc-block:nth-of-type(4)::before { animation-delay: 0.8s; }
</style>
</head>'''

if si != -1 and ei != -1:
    content = content[:si] + new_css + content[ei + len(end_marker):]
    print("OK - luz movida para FORA do card (halo ao redor)")
else:
    print("ERRO - CSS anterior nao encontrado")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Arquivo salvo")
