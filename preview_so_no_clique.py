# Faz o preview aparecer SO quando o usuario clica no botao Pre-visualizar
import re, subprocess, os, sys
path = "front/chat.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in content else "\n"

# 1. Remover processProjectData automatico
old1 = "                        // Envia conteúdo direto para o preview e oculta balão de chat" + eol + "                        processProjectData({ html_base64: htmlBase64 });"
new1 = "                        // NAO renderiza preview automaticamente - guarda para o clique no botao" + eol + "                        window.__pendingPreviewHtml = htmlBase64;"
if content.count(old1) != 1:
    print("FALHOU old1:", content.count(old1)); sys.exit(1)
content = content.replace(old1, new1, 1)

# 2. Remover oculta chat automatico
old2 = "                        // Oculta chat (previewContainer já será ativado pelo performTransition)" + eol + "                        if (chatMessages) chatMessages.classList.add('hidden');"
new2 = "                        // Chat continua visivel ate o usuario clicar em pre-visualizar"
if content.count(old2) == 1:
    content = content.replace(old2, new2, 1)

# 3. Remover performTransition automatico - usar contexto UNICO (scrollHeight antes)
old3 = "                        if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;" + eol + eol + "                        performTransition();"
new3 = "                        if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;" + eol + eol + "                        // performTransition sera chamado no clique do botao"
if content.count(old3) != 1:
    print("FALHOU old3:", content.count(old3)); sys.exit(1)
content = content.replace(old3, new3, 1)

# 4. Botao chama processProjectData + performTransition ao clicar
old_btn = '''                              <button class="aron-preview-btn" onclick="(function(){
                                var pc = document.getElementById('preview-container');
                                if(pc){ pc.classList.add('active'); pc.style.display='block'; }
                                var cm = document.getElementById('chat-messages');
                                if(cm){ cm.style.display='none'; }
                              })()">'''.replace("\n", eol)
new_btn = '''                              <button class="aron-preview-btn" onclick="(function(){
                                if(window.__pendingPreviewHtml){ processProjectData({ html_base64: window.__pendingPreviewHtml }); }
                                var cm = document.getElementById('chat-messages');
                                if(cm){ cm.classList.add('hidden'); cm.style.display='none'; }
                                if(typeof performTransition==='function'){ performTransition(); }
                                var pc = document.getElementById('preview-container');
                                if(pc){ pc.classList.add('active'); pc.style.display='block'; }
                              })()">'''.replace("\n", eol)
if content.count(old_btn) != 1:
    print("FALHOU old_btn:", content.count(old_btn)); sys.exit(1)
content = content.replace(old_btn, new_btn, 1)

scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", content, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "/tmp/pw%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; print("JS ERRO", i, r.stderr[:150])
    try: os.remove(t)
    except: pass

if ok:
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
    print("OK - preview so aparece ao clicar no botao")
else:
    print("JS invalido"); sys.exit(1)
