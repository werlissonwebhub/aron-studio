# 2/2 — FRONTEND: aba Conta deixa de mostrar dados fake (Desenvolvedor / ENTERPRISE /
# Ilimitado / 3) e passa a mostrar o usuario real: nome, email, iniciais no avatar,
# plano ativo, creditos disponiveis e total de projetos.
# RODE O 1_conta_backend.py ANTES DESTE.
import shutil, os
if os.path.exists("front/chat.html"):
    shutil.copy("front/chat.html", "front/chat.html.contabak")
    print("backup: front/chat.html.contabak")
    print()

import re, subprocess, os, sys

path = "front/chat.html"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in c else "\n"

if "acc-user-name" in c:
    print("Ja aplicado"); sys.exit(0)

# ---------- 1. Dar IDs aos elementos (trocar valores fake) ----------
trocas = [
    ('<div class="account-avatar">DV</div>',
     '<div class="account-avatar" id="acc-avatar">--</div>'),

    ('<div style="font-size: 12px; color: #71717a;">dev@aronstudio.com</div>',
     '<div style="font-size: 12px; color: #71717a;" id="acc-user-email">--</div>'),

    ('<span style="font-size: 14px; font-weight: 600; color: #34D7DD;">&#8734; Ilimitado</span>',
     '<span style="font-size: 14px; font-weight: 600; color: #34D7DD;" id="acc-credits">--</span>'),

    ('<span style="font-size: 14px; font-weight: 600; color: #a1a1aa;">3</span>',
     '<span style="font-size: 14px; font-weight: 600; color: #a1a1aa;" id="acc-projects">--</span>'),
]

feitas = []
for old, new in trocas:
    if c.count(old) == 1:
        c = c.replace(old, new, 1)
        feitas.append(old[:38])

# O nome "Desenvolvedor" esta quebrado em duas linhas no HTML
m = re.search(r'(<div style="font-size: 16px; font-weight: 600; color: #fff; margin-bottom[^>]*>)\s*Desenvolvedor</div>', c)
if m:
    tag = m.group(1)
    nova_tag = tag[:-1] + ' id="acc-user-name">'
    c = c.replace(m.group(0), nova_tag + "--</div>", 1)
    feitas.append("nome do usuario")

# O badge do plano (ENTERPRISE) — pegar a linha inteira com regex
m2 = re.search(r'(<span\s+style="padding: 4px 14px; background: linear-gradient[^>]*>)([^<]*)</span>', c)
if m2:
    nova = m2.group(1)[:-1] + ' id="acc-plan">--</span>'
    c = c.replace(m2.group(0), nova, 1)
    feitas.append("badge do plano")

# Sublabels dinamicos
c = c.replace('<div class="setting-sublabel">Acesso ilimitado a todos os modelos.</div>',
              '<div class="setting-sublabel" id="acc-plan-desc">--</div>', 1)
c = c.replace('<div class="setting-sublabel">Ciclo mensal reinicia em 30 dias.</div>',
              '<div class="setting-sublabel" id="acc-credits-desc">Creditos disponiveis para gerar.</div>', 1)

print("IDs aplicados:", len(feitas))
for f in feitas:
    print("  +", f)

# ---------- 2. Funcao que carrega os dados reais ----------
anchor = "                window.sendPrompt = sendPrompt;"
if c.count(anchor) != 1:
    print("FALHOU: ancora sendPrompt"); sys.exit(1)

func = '''
                // ===== Aba CONTA: dados reais do usuario logado =====
                const PLANOS_INFO = {
                    free:    { nome: 'FREE',    desc: 'Plano gratuito. Adquira creditos para gerar mais.' },
                    starter: { nome: 'STARTER', desc: 'Acesso aos modelos padrao.' },
                    pro:     { nome: 'PRO',     desc: 'Acesso a todos os modelos, incluindo premium.' },
                    ultra:   { nome: 'ULTRA',   desc: 'Acesso ilimitado a todos os modelos.' }
                };

                window.carregarDadosConta = async function() {
                    const uid = localStorage.getItem('aron_user_id');
                    if (!uid) return;

                    // Nome, email e avatar vem do Firebase (usuario logado)
                    try {
                        const u = (typeof firebase !== 'undefined' && firebase.auth) ? firebase.auth().currentUser : null;
                        if (u) {
                            const nome = u.displayName || (u.email ? u.email.split('@')[0] : 'Usuario');
                            const elNome = document.getElementById('acc-user-name');
                            const elMail = document.getElementById('acc-user-email');
                            const elAv   = document.getElementById('acc-avatar');
                            if (elNome) elNome.textContent = nome;
                            if (elMail) elMail.textContent = u.email || '';
                            if (elAv) {
                                const partes = nome.trim().split(/\\s+/);
                                const ini = (partes[0][0] || '') + (partes.length > 1 ? partes[partes.length-1][0] : '');
                                elAv.textContent = ini.toUpperCase();
                            }
                        }
                    } catch (e) { console.error('conta: firebase', e); }

                    // Plano, creditos e projetos vem da API
                    try {
                        const r = await apiFetch(`${API_URL}/api/user/me?user_id=${uid}`);
                        if (!r.ok) return;
                        const d = await r.json();

                        const plano = (d.plan || 'free').toLowerCase();
                        const info = PLANOS_INFO[plano] || PLANOS_INFO.free;

                        const elPlan = document.getElementById('acc-plan');
                        if (elPlan) elPlan.textContent = info.nome;

                        const elPlanDesc = document.getElementById('acc-plan-desc');
                        if (elPlanDesc) elPlanDesc.textContent = info.desc;

                        const elCred = document.getElementById('acc-credits');
                        if (elCred) {
                            const cred = d.credits;
                            if (plano === 'ultra' || cred >= 99999) {
                                elCred.textContent = '\\u221E Ilimitado';
                            } else {
                                elCred.textContent = cred + (cred === 1 ? ' credito' : ' creditos');
                                elCred.style.color = cred <= 3 ? '#f87171' : '#34D7DD';
                            }
                        }

                        const elProj = document.getElementById('acc-projects');
                        if (elProj) elProj.textContent = (d.projects_count != null ? d.projects_count : '0');
                    } catch (e) {
                        console.error('conta: api', e);
                    }
                };

'''.replace("\n", eol)

c = c.replace(anchor, func + anchor, 1)
print("  + funcao carregarDadosConta()")

# ---------- 3. Chamar ao abrir as configuracoes ----------
# procurar a funcao que abre o modal
m3 = re.search(r"window\.openSettings\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{|window\.openSettings\s*=\s*(?:async\s*)?function\s*\([^)]*\)\s*\{|function openSettings\s*\([^)]*\)\s*\{", c)
if m3:
    ponto = m3.end()
    ins = eol + "                    if (window.carregarDadosConta) window.carregarDadosConta();"
    c = c[:ponto] + ins + c[ponto:]
    print("  + chamada ao abrir Configuracoes")
else:
    print("  ! openSettings nao encontrada — a funcao existe mas nao sera chamada automaticamente")

# ---------- validar ----------
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", c, re.DOTALL)
ok = True
for i, s in enumerate(scripts):
    t = "/tmp/cc%d.js" % i
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; print("JS ERRO", i, r.stderr[:200])
    try: os.remove(t)
    except: pass

if ok:
    with open(path, "wb") as f:
        f.write(c.encode("utf-8"))
    print()
    print("OK - aba Conta agora usa dados reais")
else:
    print("NADA SALVO"); sys.exit(1)
