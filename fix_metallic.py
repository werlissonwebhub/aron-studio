path = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Substitui o <p> do titulo principal por versao com gradiente metalico
old = '''                <p
                    class="text-4xl md:text-5xl font-black tracking-tighter max-w-4xl mx-auto leading-[1.05] text-[#8A3FFC]">
                    The Future of the Web <br> <span class="text-[#34D7DD]">Engineering and Design.</span>
                </p>'''

new = '''                <p class="aron-metallic-title text-4xl md:text-5xl font-black tracking-tighter max-w-4xl mx-auto leading-[1.05]">
                    The Future of the Web <br> <span>Engineering and Design.</span>
                </p>'''

if old in content:
    content = content.replace(old, new)
    print("FIX1 (titulo) OK")
else:
    print("FIX1 FALHOU")

# Adiciona o CSS do efeito metalico antes do </head>
css = '''<style>
/* Efeito metalico cromado - combina com a logo Aron */
.aron-metallic-title {
    background: linear-gradient(180deg, #ffffff 0%, #e8ecf1 25%, #b8c2cc 50%, #ffffff 62%, #9aa6b2 78%, #dfe6ec 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
    filter: drop-shadow(0 2px 8px rgba(180, 200, 230, 0.25));
    background-size: 100% 200%;
    animation: aronMetallicShine 6s ease-in-out infinite;
}
.aron-metallic-title span {
    background: linear-gradient(180deg, #eafcff 0%, #a9e8ef 30%, #5fb8c4 55%, #eafcff 68%, #7fd4de 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
}
@keyframes aronMetallicShine {
    0%, 100% { background-position: 0% 0%; }
    50% { background-position: 0% 100%; }
}
</style>
</head>'''

if '</head>' in content:
    content = content.replace('</head>', css, 1)
    print("FIX2 (CSS) OK")
else:
    print("FIX2 FALHOU")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Arquivo salvo")
