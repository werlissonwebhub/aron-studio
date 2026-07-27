# CORRECAO CRITICA: salvar o projeto no banco ao terminar a geracao
# (sem isso a IA nao reconhece o codigo e recria o site do zero)
import re, subprocess, os, sys
path = "front/chat.html"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in content else "\n"

# Localizar onde guardamos o html pendente e adicionar o SALVAMENTO automatico
old = ("                        // NAO renderiza preview automaticamente - guarda para o clique no botao" + eol +
       "                        window.__pendingPreviewHtml = htmlBase64;")

new = ("                        // NAO renderiza preview automaticamente - guarda para o clique no botao" + eol +
       "                        window.__pendingPreviewHtml = htmlBase64;" + eol +
       eol +
       "                        // MAS salva o projeto no banco imediatamente (essencial para a IA" + eol +
       "                        // reconhecer o codigo em modificacoes futuras)" + eol +
       "                        try {" + eol +
       "                            const _decoded = decodeURIComponent(escape(atob(htmlBase64)));" + eol +
       "                            if (window.__aronSetFullHtml) window.__aronSetFullHtml(_decoded);" + eol +
       "                            if (window.saveProjectToCloud) window.saveProjectToCloud(true);" + eol +
       "                        } catch (_eSave) {" + eol +
       "                            try {" + eol +
       "                                const _d2 = atob(htmlBase64);" + eol +
       "                                if (window.__aronSetFullHtml) window.__aronSetFullHtml(_d2);" + eol +
       "                                if (window.saveProjectToCloud) window.saveProjectToCloud(true);" + eol +
       "                            } catch (_e2) { console.error('Falha ao salvar projeto:', _e2); }" + eol +
       "                        }")

if content.count(old) != 1:
    print("FALHOU: bloco pendingPreviewHtml nao encontrado (", content.count(old), ")")
    sys.exit(1)

content = content.replace(old, new, 1)

scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", content, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "/tmp/sv%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; print("JS ERRO", i, r.stderr[:150])
    try: os.remove(t)
    except: pass

if ok:
    with open(path, "wb") as f:
        f.write(content.encode("utf-8"))
    print("OK - projeto agora e salvo automaticamente ao terminar a geracao")
else:
    print("JS invalido"); sys.exit(1)
