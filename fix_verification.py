path = r'C:\Users\w7\OneDrive\Área de Trabalho\ARON_STUDIO\server\main.py'
old = '@app.get("/chat")'
new = '@app.get("/google022d0f40a84805e0.html")\nasync def google_verification():\n    return FileResponse("../front/google022d0f40a84805e0.html")\n\n@app.get("/chat")'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK - rota de verificacao adicionada')
else:
    print('ERRO - linha nao encontrada')
