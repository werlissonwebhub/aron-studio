# O painel de codigo ficava vazio ("Nenhum codigo gerado ainda") ao abrir um
# projeto salvo — mesmo com o codigo presente no banco (62k+ chars).
#
# CAUSA: em loadProjectFromCloud existem dois caminhos.
#   - Sem full_json: seta fullHtml + preenche o editor  (funcionava)
#   - Com full_json: SO renderizava o preview e esquecia de setar o fullHtml
#     e o editor  (era o caso dos seus projetos)
#
# CORRECAO: o caminho do full_json agora tambem extrai o HTML, seta o fullHtml
# e preenche o painel de codigo.
#
# EFEITO COLATERAL BOM: o fullHtml passa a ser setado ao abrir um projeto — o
# que tambem faz o editor manual e o salvamento funcionarem em projetos abertos
# da lista (antes eles nao tinham o HTML em memoria).
import shutil, os
if os.path.exists("front/chat.html"):
    shutil.copy("front/chat.html", "front/chat.html.loadbak")
    print("backup: front/chat.html.loadbak")
    print()

import re, subprocess, os, sys

path = "front/chat.html"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in c else "\n"

if "__loadPreencheCodigo" in c:
    print("Ja aplicado"); sys.exit(0)

old = """                    if (p.full_json) {
                        try {
                            const projectData = JSON.parse(p.full_json);
                            if (window.renderMultiFileApp) {
                                if (projectData.project_structure) {
                                    window.renderMultiFileApp(projectData.project_structure);
                                } else {
                                    window.renderMultiFileApp(projectData);
                                }
                            }
                        } catch (parseErr) {""".replace("\n", eol)

new = """                    if (p.full_json) {
                        try {
                            const projectData = JSON.parse(p.full_json);
                            if (window.renderMultiFileApp) {
                                if (projectData.project_structure) {
                                    window.renderMultiFileApp(projectData.project_structure);
                                } else {
                                    window.renderMultiFileApp(projectData);
                                }
                            }

                            // __loadPreencheCodigo — o painel de codigo ficava vazio ("Nenhum codigo
                            // gerado ainda") porque este caminho so renderizava o preview e nunca
                            // setava o fullHtml nem o editor.
                            var _htmlProj = '';
                            var _est = projectData.project_structure || projectData;
                            if (_est && typeof _est === 'object') {
                                _htmlProj = _est.html || _est.index_html || _est['index.html'] || '';
                            }
                            if (!_htmlProj && p.html_code) _htmlProj = p.html_code;
                            if (!_htmlProj && typeof projectData === 'string') _htmlProj = projectData;

                            if (_htmlProj) {
                                fullHtml = _htmlProj;
                                if (window.__aronSetFullHtml) window.__aronSetFullHtml(_htmlProj);
                                window.fullHtml = _htmlProj;
                                if (window.monacoEditor) {
                                    try { window.monacoEditor.setValue(_htmlProj); } catch (e) {}
                                }
                                if (typeof window.updateCodePanel === 'function') {
                                    try { window.updateCodePanel(_htmlProj); } catch (e) {}
                                }
                            }
                            window.currentProjectData = projectData;
                        } catch (parseErr) {""".replace("\n", eol)

if c.count(old) != 1:
    print("FALHOU: bloco nao encontrado (", c.count(old), ")"); sys.exit(1)

c = c.replace(old, new, 1)

scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", c, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "/tmp/lp%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; print("JS ERRO", i, r.stderr[:200])
    try: os.remove(t)
    except: pass

if not ok:
    print("NADA SALVO"); sys.exit(1)

with open(path, "wb") as f:
    f.write(c.encode("utf-8"))

print("OK - ao abrir um projeto, o painel de codigo agora e preenchido")
print()
print("O que era: o caminho do full_json so renderizava o preview e esquecia")
print("de setar o fullHtml / o editor. Por isso o painel dizia 'Nenhum codigo")
print("gerado ainda' mesmo com o codigo salvo no banco.")
print()
print("Sintaxe JS: valida")
