path = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============ PARTE 1: Titulo metalico ============
old_title = '''                <p
                    class="text-4xl md:text-5xl font-black tracking-tighter max-w-4xl mx-auto leading-[1.05] text-[#8A3FFC]">
                    The Future of the Web <br> <span class="text-[#34D7DD]">Engineering and Design.</span>
                </p>'''

new_title = '''                <p class="aron-metallic-title text-4xl md:text-5xl font-black tracking-tighter max-w-4xl mx-auto leading-[1.05]">
                    The Future of the Web <br> <span>Engineering and Design.</span>
                </p>'''

part1 = "OK" if old_title in content else "FALHOU"
content = content.replace(old_title, new_title)

# ============ PARTE 2: CSS ============
css = '''<style>
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

/* ===== Luz brilhante que varre os cards grandes (estilo huly) ===== */
#showcase-criar .sc-block {
    position: relative;
    overflow: hidden;
    isolation: isolate;
}
/* A luz que se move suavemente pelo card */
#showcase-criar .sc-block::after {
    content: "";
    position: absolute;
    top: -50%;
    left: -60%;
    width: 60%;
    height: 200%;
    background: linear-gradient(105deg,
        transparent 0%,
        rgba(138,63,252,0.06) 25%,
        rgba(52,215,221,0.14) 45%,
        rgba(191,224,255,0.20) 50%,
        rgba(52,215,221,0.14) 55%,
        rgba(138,63,252,0.06) 75%,
        transparent 100%);
    filter: blur(20px);
    transform: rotate(8deg);
    pointer-events: none;
    z-index: 0;
    animation: aronLightSweep 7s ease-in-out infinite;
}
/* Mantem o conteudo acima da luz */
#showcase-criar .sc-block > * { position: relative; z-index: 1; }
@keyframes aronLightSweep {
    0%   { left: -60%; opacity: 0; }
    15%  { opacity: 1; }
    85%  { opacity: 1; }
    100% { left: 110%; opacity: 0; }
}
/* Delay diferente por card, pra luz nao passar em todos ao mesmo tempo */
#showcase-criar .sc-block:nth-of-type(2)::after { animation-delay: 2.3s; }
#showcase-criar .sc-block:nth-of-type(3)::after { animation-delay: 4.6s; }
#showcase-criar .sc-block:nth-of-type(4)::after { animation-delay: 1.2s; }
</style>
</head>'''

part2 = "OK" if '</head>' in content else "FALHOU"
content = content.replace('</head>', css, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Titulo metalico: {part1}")
print(f"CSS luz + metalico: {part2}")
print("Arquivo salvo")
