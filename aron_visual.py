path = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ============ PARTE 1: Metalico no titulo ============
old_title = '''                <p
                    class="text-4xl md:text-5xl font-black tracking-tighter max-w-4xl mx-auto leading-[1.05] text-[#8A3FFC]">
                    The Future of the Web <br> <span class="text-[#34D7DD]">Engineering and Design.</span>
                </p>'''

new_title = '''                <p class="aron-metallic-title text-4xl md:text-5xl font-black tracking-tighter max-w-4xl mx-auto leading-[1.05]">
                    The Future of the Web <br> <span>Engineering and Design.</span>
                </p>'''

part1 = "OK" if old_title in content else "FALHOU"
content = content.replace(old_title, new_title)

# ============ PARTE 2: CSS (metalico + borda brilhante) ============
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

/* ===== Borda brilhante ao redor do card (roxo + azul) ===== */
.feature-card {
    position: relative;
    border-radius: 16px;
    background: #0d0d14;
    z-index: 0;
}
/* A borda animada girando ao redor */
.feature-card::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 16px;
    padding: 1.5px;
    background: conic-gradient(from var(--aron-angle, 0deg),
        transparent 0%,
        #8A3FFC 15%,
        #34D7DD 30%,
        transparent 45%,
        transparent 100%);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask-composite: exclude;
    opacity: 0.5;
    transition: opacity 0.4s ease;
    animation: aronBorderSpin 5s linear infinite;
    pointer-events: none;
}
.feature-card:hover::before { opacity: 1; }
@property --aron-angle {
    syntax: "<angle>";
    initial-value: 0deg;
    inherits: false;
}
@keyframes aronBorderSpin {
    to { --aron-angle: 360deg; }
}
</style>
</head>'''

part2 = "OK" if '</head>' in content else "FALHOU"
content = content.replace('</head>', css, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Titulo metalico: {part1}")
print(f"CSS borda+metalico: {part2}")
print("Arquivo salvo")
