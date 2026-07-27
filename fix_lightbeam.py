path = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# CSS do efeito light beam (estilo huly.io) nas cores roxo/azul
css = '''<style>
/* ===== Light Beam Effect (estilo huly.io) - cores roxo + azul Aron ===== */
.feature-card {
    position: relative;
    overflow: hidden;
    isolation: isolate;
}
/* O feixe de luz vertical que sobe do centro-base do card */
.feature-card::before {
    content: "";
    position: absolute;
    left: 50%;
    bottom: 0;
    width: 2px;
    height: 70%;
    transform: translateX(-50%);
    background: linear-gradient(to top, rgba(138,63,252,0) 0%, rgba(138,63,252,0.9) 30%, rgba(52,215,221,0.9) 70%, rgba(191,224,255,0) 100%);
    filter: blur(1px);
    opacity: 0;
    transition: opacity 0.5s ease;
    z-index: 0;
    pointer-events: none;
}
/* O glow radial que se espalha da base do feixe */
.feature-card::after {
    content: "";
    position: absolute;
    left: 50%;
    bottom: -40%;
    width: 80%;
    height: 90%;
    transform: translateX(-50%);
    background: radial-gradient(ellipse at center, rgba(90,79,176,0.55) 0%, rgba(52,215,221,0.25) 35%, transparent 70%);
    filter: blur(24px);
    opacity: 0;
    transition: opacity 0.5s ease;
    z-index: 0;
    pointer-events: none;
}
/* Ao passar o mouse: acende o feixe e o glow */
.feature-card:hover::before { opacity: 1; }
.feature-card:hover::after { opacity: 1; }
/* Garante que o conteudo fica acima da luz */
.feature-card > * { position: relative; z-index: 1; }
/* Animacao suave de respiracao permanente e sutil */
@keyframes aronBeamBreath {
    0%, 100% { opacity: 0.35; }
    50% { opacity: 0.6; }
}
.feature-card::before { animation: aronBeamBreath 4s ease-in-out infinite; opacity: 0.35; }
.feature-card::after { animation: aronBeamBreath 4s ease-in-out infinite; opacity: 0.25; }
.feature-card:hover::before { opacity: 1 !important; animation: none; }
.feature-card:hover::after { opacity: 1 !important; animation: none; }
</style>
</head>'''

if '</head>' in content:
    content = content.replace('</head>', css, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK - efeito light beam adicionado")
else:
    print("ERRO - </head> nao encontrado")
