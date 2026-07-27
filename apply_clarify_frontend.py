import re

path = "front/chat.html"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

if "api/clarify" in content:
    print("Clarify JA EXISTE - nada feito")
    raise SystemExit

CR = "\r\n"

# ============ PARTE 1: bloco no sendPrompt ============
A1 = "                    if (!isRetry) lastUsedPrompt = prompt;" + CR
if content.count(A1) != 1:
    print("ancora 1 falhou:", content.count(A1)); raise SystemExit

b1 = [
"",
"                    // -- MODO ENTREVISTA (clarify) --",
"                    if (!isRetry && !window.__clarifyResolved) {",
"                        try {",
"                            let _ctok = null;",
"                            try {",
"                                if (typeof firebase !== 'undefined' && firebase.auth && firebase.auth().currentUser) {",
"                                    _ctok = await firebase.auth().currentUser.getIdToken();",
"                                }",
"                            } catch (te) {}",
"                            const _chd = { 'Content-Type': 'application/json' };",
"                            if (_ctok) _chd['Authorization'] = 'Bearer ' + _ctok;",
"                            const cRes = await fetch(API_URL + '/api/clarify', {",
"                                method: 'POST', headers: _chd,",
"                                body: JSON.stringify({ prompt: prompt, user_id: userId })",
"                            });",
"                            if (cRes.ok) {",
"                                const cData = await cRes.json();",
"                                if (cData && cData.ready === false && Array.isArray(cData.questions) && cData.questions.length) {",
"                                    isSending = false; resetSendButton();",
"                                    renderClarifyQuestions(cData.questions, prompt); return;",
"                                }",
"                            }",
"                        } catch (e) {}",
"                    }",
"                    window.__clarifyResolved = false;",
"",
]
content = content.replace(A1, A1 + CR.join(b1) + CR, 1)

# ============ PARTE 2: funcoes auxiliares ============
A2 = "                window.sendPrompt = sendPrompt;" + CR
if content.count(A2) != 1:
    print("ancora 2 falhou:", content.count(A2)); raise SystemExit

# Strings longas montadas por concatenacao curta
SUB = ("'<button id=\"clarify-submit\" style=\"margin-top:8px;width:100%;"
       "padding:12px;background:linear-gradient(135deg,#8A3FFC,#34D7DD);"
       "color:#fff;border:none;border-radius:10px;font-weight:700;"
       "font-size:14px;cursor:pointer\">Gerar meu projeto</button>'")
SKIP = ("'<button id=\"clarify-skip\" style=\"margin-top:8px;width:100%;"
        "padding:10px;background:transparent;color:#71717a;border:none;"
        "font-size:13px;cursor:pointer\">Pular e gerar direto</button>'")
BTNCSS = ("'padding:8px 14px;background:rgba(255,255,255,0.05);"
          "border:1px solid rgba(255,255,255,0.1);color:#d4d4d8;"
          "border-radius:20px;font-size:13px;cursor:pointer;transition:all .2s'")
INPCSS = ("'width:100%;padding:10px 12px;background:rgba(255,255,255,0.05);"
          "border:1px solid rgba(255,255,255,0.1);color:#fff;"
          "border-radius:8px;font-size:13px'")

b2 = [
"                // -- Funcoes do Modo Entrevista --",
"                function renderClarifyQuestions(questions, originalPrompt) {",
"                    const welcome = document.getElementById('welcome-studio');",
"                    if (welcome) welcome.classList.remove('active');",
"                    const chatMessages = document.getElementById('chat-messages');",
"                    if (!chatMessages) return;",
"                    chatMessages.classList.remove('hidden');",
"                    chatMessages.style.display = 'block';",
"                    chatMessages.innerHTML = '';",
"                    const wrap = document.createElement('div');",
"                    wrap.className = 'aron-msg-row';",
"                    wrap.innerHTML = '<div class=\"aron-bubble\" style=\"max-width:640px;width:100%\">'",
"                        + '<div style=\"color:#a78bfa;font-size:12px;letter-spacing:.08em;font-family:monospace;margin-bottom:14px\">ALGUMAS PERGUNTAS RAPIDAS</div>'",
"                        + '<div style=\"color:#e4e4e7;font-size:14px;margin-bottom:18px\">Pra criar seu projeto do jeito certo, me responde isso:</div>'",
"                        + '<div id=\"clarify-questions\"></div>'",
"                        + " + SUB,
"                        + " + SKIP + ";",
"                    chatMessages.appendChild(wrap);",
"                    const qContainer = document.getElementById('clarify-questions');",
"                    window.__clarifyState = { questions: questions, answers: {}, originalPrompt: originalPrompt };",
"                    questions.forEach(function(q, idx) {",
"                        const qDiv = document.createElement('div');",
"                        qDiv.style.cssText = 'margin-bottom:18px';",
"                        const label = document.createElement('div');",
"                        label.textContent = q.pergunta;",
"                        label.style.cssText = 'color:#d4d4d8;font-size:13px;margin-bottom:8px;font-weight:600';",
"                        qDiv.appendChild(label);",
"                        if (q.tipo === 'botoes' && Array.isArray(q.opcoes) && q.opcoes.length) {",
"                            const btnWrap = document.createElement('div');",
"                            btnWrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px';",
"                            q.opcoes.forEach(function(op) {",
"                                const b = document.createElement('button');",
"                                b.textContent = op;",
"                                b.style.cssText = " + BTNCSS + ";",
"                                b.onclick = function() {",
"                                    window.__clarifyState.answers[q.id || ('q'+idx)] = { pergunta: q.pergunta, resposta: op };",
"                                    Array.from(btnWrap.children).forEach(function(c){ c.style.background='rgba(255,255,255,0.05)'; c.style.color='#d4d4d8'; });",
"                                    b.style.background = 'linear-gradient(135deg,#8A3FFC,#34D7DD)';",
"                                    b.style.color = '#fff';",
"                                };",
"                                btnWrap.appendChild(b);",
"                            });",
"                            qDiv.appendChild(btnWrap);",
"                        } else {",
"                            const inp = document.createElement('input');",
"                            inp.type = 'text'; inp.placeholder = 'Digite sua resposta...';",
"                            inp.style.cssText = " + INPCSS + ";",
"                            inp.oninput = function() {",
"                                window.__clarifyState.answers[q.id || ('q'+idx)] = { pergunta: q.pergunta, resposta: inp.value };",
"                            };",
"                            qDiv.appendChild(inp);",
"                        }",
"                        qContainer.appendChild(qDiv);",
"                    });",
"                    document.getElementById('clarify-submit').onclick = function() { submitClarifyAnswers(false); };",
"                    document.getElementById('clarify-skip').onclick = function() { submitClarifyAnswers(true); };",
"                }",
"                function submitClarifyAnswers(skip) {",
"                    const st = window.__clarifyState;",
"                    if (!st) return;",
"                    let enriched = st.originalPrompt;",
"                    if (!skip) {",
"                        const parts = [];",
"                        Object.keys(st.answers).forEach(function(k) {",
"                            const a = st.answers[k];",
"                            if (a && a.resposta && a.resposta.trim()) parts.push('- ' + a.pergunta + ' ' + a.resposta);",
"                        });",
"                        if (parts.length) enriched = st.originalPrompt + '\\n\\nDETALHES ADICIONAIS:\\n' + parts.join('\\n');",
"                    }",
"                    window.__clarifyResolved = true;",
"                    textarea.value = enriched;",
"                    window.__clarifyState = null;",
"                    sendPrompt(false);",
"                }",
"",
]
content = content.replace(A2, CR.join(b2) + CR + A2, 1)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

# validar JS
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", content, re.DOTALL)
import subprocess, os
ok = True
for i, s in enumerate(scripts):
    t = "_v%d.js" % i
    with open(t, "w", encoding="utf-8") as f: f.write(s)
    try:
        r = subprocess.run(["node","--check",t], capture_output=True, text=True)
        if r.returncode != 0: ok = False; print("JS ERRO bloco", i, r.stderr[:150])
    except FileNotFoundError: pass
    finally:
        if os.path.exists(t): os.remove(t)
print("PARTE 1 e 2 inseridas")
print("Sintaxe JS valida:", ok)
print("ARQUIVO SALVO: front/chat.html")
