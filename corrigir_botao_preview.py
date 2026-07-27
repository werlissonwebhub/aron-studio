# CORRECAO URGENTE: botao de pre-visualizar nao funcionava (processProjectData nao era global)
import re, subprocess, os, sys
path = "front/chat.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in content else "\n"

# 1. Expor processProjectData globalmente (logo apos sua definicao)
old_def = "                function processProjectData(data) {"
new_def = "                function processProjectData(data) {"
if content.count(old_def) != 1:
    print("FALHOU: definicao processProjectData nao encontrada"); sys.exit(1)

# Adicionar window.processProjectData = processProjectData; logo antes de window.sendPrompt
anchor = "                window.sendPrompt = sendPrompt;"
if content.count(anchor) != 1:
    print("FALHOU: ancora sendPrompt"); sys.exit(1)
expose = "                window.processProjectData = processProjectData;" + eol
if "window.processProjectData" not in content:
    content = content.replace(anchor, expose + anchor, 1)
    print("processProjectData exposto em window")

# 2. Corrigir o botao: usar window.processProjectData e REMOVER performTransition (nao existe no escopo global)
old_btn = '''                              <button class="aron-preview-btn" onclick="(function(){
                                if(window.__pendingPreviewHtml){ processProjectData({ html_base64: window.__pendingPreviewHtml }); }
                                var cm = document.getElementById('chat-messages');
                                if(cm){ cm.classList.add('hidden'); cm.style.display='none'; }
                                if(typeof performTransition==='function'){ performTransition(); }
                                var pc = document.getElementById('preview-container');
                                if(pc){ pc.classList.add('active'); pc.style.display='block'; }
                              })()">'''.replace("\n", eol)

new_btn = '''                              <button class="aron-preview-btn" onclick="(function(){
                                if(window.__pendingPreviewHtml && window.processProjectData){ window.processProjectData({ html_base64: window.__pendingPreviewHtml }); }
                                var cm = document.getElementById('chat-messages');
                                if(cm){ cm.classList.add('hidden'); cm.style.display='none'; }
                                var pc = document.getElementById('preview-container');
                                if(pc){ pc.classList.add('active'); pc.style.display='block'; }
                              })()">'''.replace("\n", eol)

if content.count(old_btn) != 1:
    print("FALHOU: botao nao encontrado (", content.count(old_btn), ")"); sys.exit(1)
content = content.replace(old_btn, new_btn, 1)
print("botao corrigido (usa window.processProjectData, sem performTransition)")

# validar
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", content, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "/tmp/bt%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; print("JS ERRO", i, r.stderr[:150])
    try: os.remove(t)
    except: pass

if ok:
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
    print("OK - botao de preview corrigido")
else:
    print("JS invalido"); sys.exit(1)
