# Equalizador de voz no microfone.
# A transcricao (Web Speech API, pt-BR) ja existia e funcionava — faltava so o
# feedback visual. Agora, ao gravar, aparecem 12 barras verticais que sobem e
# descem conforme o VOLUME REAL da voz (Web Audio API), com um indicador
# "Ouvindo..." e ponto vermelho pulsante.
import shutil, os
if os.path.exists("front/chat.html"):
    shutil.copy("front/chat.html", "front/chat.html.micbak")
    print("backup: front/chat.html.micbak")
    print()

import re, subprocess, os, sys

path = "front/chat.html"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in c else "\n"

if "aron-voice-bars" in c:
    print("Ja aplicado"); sys.exit(0)

# ---------- 1. CSS das barras ----------
css = """
        /* ===== Equalizador de voz (gravacao por microfone) ===== */
        #aron-voice-bars {
            display: none;
            align-items: center;
            gap: 3px;
            height: 26px;
            padding: 0 10px;
        }

        #aron-voice-bars.on {
            display: flex;
        }

        #aron-voice-bars .vb {
            width: 3px;
            min-height: 3px;
            height: 3px;
            border-radius: 2px;
            background: linear-gradient(180deg, #34D7DD, #8A3FFC);
            transition: height 70ms linear;
        }

        #aron-voice-label {
            display: none;
            align-items: center;
            gap: 7px;
            font-size: 11px;
            color: #34D7DD;
            font-family: 'JetBrains Mono', monospace;
            white-space: nowrap;
        }

        #aron-voice-label.on {
            display: flex;
        }

        #aron-voice-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #ef4444;
            animation: aron-rec-pulse 1.1s ease-in-out infinite;
        }

        @keyframes aron-rec-pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: .35; transform: scale(.8); }
        }
"""
css = css.replace("\n", eol)

fim_style = c.find("</style>")
if fim_style == -1:
    print("FALHOU: </style> nao encontrado"); sys.exit(1)
c = c[:fim_style] + css + c[fim_style:]

# ---------- 2. HTML: inserir as barras ao lado do botao do mic ----------
anchor_html = '<button type="button" id="mic-btn" onclick="toggleRecording()"'
i = c.find(anchor_html)
if i == -1:
    print("FALHOU: botao do mic nao encontrado"); sys.exit(1)

# achar o fim da tag <button ...> </button>
fim_btn = c.find("</button>", i)
if fim_btn == -1:
    print("FALHOU: fechamento do botao"); sys.exit(1)
fim_btn += len("</button>")

barras = (eol +
    '                            <div id="aron-voice-bars">' + eol +
    '                                <span class="vb"></span><span class="vb"></span><span class="vb"></span>' + eol +
    '                                <span class="vb"></span><span class="vb"></span><span class="vb"></span>' + eol +
    '                                <span class="vb"></span><span class="vb"></span><span class="vb"></span>' + eol +
    '                                <span class="vb"></span><span class="vb"></span><span class="vb"></span>' + eol +
    '                            </div>' + eol +
    '                            <span id="aron-voice-label">' + eol +
    '                                <span id="aron-voice-dot"></span>Ouvindo...' + eol +
    '                            </span>')

c = c[:fim_btn] + barras + c[fim_btn:]

# ---------- 3. JS: analisar o audio e animar as barras ----------
old_stop = """                function stopRecordingUI() {
                    if (!isRecording) return;
                    isRecording = false;
                    playSciFiBeep('stop');""".replace("\n", eol)

new_stop = """                // ===== Equalizador: le o volume real do microfone =====
                let __vozStream = null, __vozCtx = null, __vozRaf = null;

                async function iniciarBarrasVoz() {
                    const wrap = document.getElementById('aron-voice-bars');
                    const label = document.getElementById('aron-voice-label');
                    if (!wrap) return;
                    wrap.classList.add('on');
                    if (label) label.classList.add('on');

                    try {
                        __vozStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        __vozCtx = new (window.AudioContext || window.webkitAudioContext)();
                        const src = __vozCtx.createMediaStreamSource(__vozStream);
                        const analyser = __vozCtx.createAnalyser();
                        analyser.fftSize = 64;
                        analyser.smoothingTimeConstant = 0.75;
                        src.connect(analyser);

                        const dados = new Uint8Array(analyser.frequencyBinCount);
                        const barras = wrap.querySelectorAll('.vb');

                        function animar() {
                            analyser.getByteFrequencyData(dados);
                            barras.forEach(function (b, idx) {
                                // distribui as frequencias entre as barras
                                const pos = Math.floor((idx / barras.length) * dados.length * 0.7) + 1;
                                const v = dados[pos] || 0;
                                const alt = Math.max(3, Math.min(24, (v / 255) * 30));
                                b.style.height = alt + 'px';
                            });
                            __vozRaf = requestAnimationFrame(animar);
                        }
                        animar();
                    } catch (e) {
                        console.error('microfone:', e);
                        // Sem permissao: anima as barras suavemente so para dar feedback
                        const barras = wrap.querySelectorAll('.vb');
                        let t = 0;
                        function fake() {
                            t += 0.18;
                            barras.forEach(function (b, i) {
                                const alt = 5 + Math.abs(Math.sin(t + i * 0.5)) * 12;
                                b.style.height = alt + 'px';
                            });
                            __vozRaf = requestAnimationFrame(fake);
                        }
                        fake();
                    }
                }

                function pararBarrasVoz() {
                    const wrap = document.getElementById('aron-voice-bars');
                    const label = document.getElementById('aron-voice-label');
                    if (wrap) {
                        wrap.classList.remove('on');
                        wrap.querySelectorAll('.vb').forEach(function (b) { b.style.height = '3px'; });
                    }
                    if (label) label.classList.remove('on');

                    if (__vozRaf) { cancelAnimationFrame(__vozRaf); __vozRaf = null; }
                    if (__vozStream) {
                        __vozStream.getTracks().forEach(function (t) { t.stop(); });
                        __vozStream = null;
                    }
                    if (__vozCtx) {
                        try { __vozCtx.close(); } catch (e) {}
                        __vozCtx = null;
                    }
                }

                function stopRecordingUI() {
                    if (!isRecording) return;
                    isRecording = false;
                    pararBarrasVoz();
                    playSciFiBeep('stop');""".replace("\n", eol)

if c.count(old_stop) != 1:
    print("FALHOU: stopRecordingUI nao encontrada"); sys.exit(1)
c = c.replace(old_stop, new_stop, 1)

# ---------- 4. Ligar as barras quando a gravacao comeca ----------
old_start = """                    recognition.onstart = function () {
                        isRecording = true;
                        playSciFiBeep('start');""".replace("\n", eol)

new_start = """                    recognition.onstart = function () {
                        isRecording = true;
                        iniciarBarrasVoz();
                        playSciFiBeep('start');""".replace("\n", eol)

if c.count(old_start) != 1:
    print("FALHOU: recognition.onstart nao encontrada"); sys.exit(1)
c = c.replace(old_start, new_start, 1)

# ---------- validar ----------
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", c, re.DOTALL)
ok = True
for i2, s in enumerate(scripts):
    t = "/tmp/mc%d.js" % i2
    open(t, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node","--check",t], capture_output=True, text=True)
    if r.returncode != 0:
        ok = False; print("JS ERRO", i2, r.stderr[:200])
    try: os.remove(t)
    except: pass

if not ok:
    print("NADA SALVO"); sys.exit(1)

with open(path, "wb") as f:
    f.write(c.encode("utf-8"))

print("OK - equalizador de voz adicionado")
print()
print("  + 12 barras verticais que reagem ao VOLUME REAL da voz (Web Audio API)")
print("  + indicador 'Ouvindo...' com ponto vermelho pulsante")
print("  + microfone e liberado corretamente ao parar (sem vazamento)")
print("  + fallback animado se o usuario negar a permissao")
print()
print("Sintaxe JS: valida")
