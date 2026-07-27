path = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\front\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove o CSS antigo (branco/prata) e substitui pelo roxo escuro + azul bebe
old_css_start = '<style>\n/* Efeito metalico cromado - combina com a logo Aron */'
old_css_end = '</style>\n</head>'

start_idx = content.find(old_css_start)
end_idx = content.find(old_css_end)

if start_idx != -1 and end_idx != -1:
    new_css = '''<style>
/* Efeito metalico roxo escuro + azul bebe - cores da logo Aron */
.aron-metallic-title {
    background: linear-gradient(180deg, #a5c8ff 0%, #6d7fd6 22%, #3d2f8f 46%, #b8d4ff 60%, #2a1f6b 80%, #8fa8f0 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
    filter: drop-shadow(0 2px 12px rgba(109, 127, 214, 0.4));
    background-size: 100% 200%;
    animation: aronMetallicShine 6s ease-in-out infinite;
}
.aron-metallic-title span {
    background: linear-gradient(180deg, #bfe0ff 0%, #7ba8e8 28%, #4a3f9e 52%, #cfe6ff 66%, #5a4fb0 100%);
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
    content = content[:start_idx] + new_css + content[end_idx + len(old_css_end):]
    print("CSS metalico atualizado (roxo + azul bebe)")
else:
    print("ERRO - CSS antigo nao encontrado")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Arquivo salvo")
