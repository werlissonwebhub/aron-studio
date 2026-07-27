# Corrige o modal de Configuracoes no mobile.
# Problema: .settings-sidebar tinha width:200px + flex-shrink:0 e o modal era
# display:flex sem media query. Numa tela de 390px a sidebar comia metade e o
# conteudo ficava espremido em ~150px, cortando os textos.
import shutil, os
if os.path.exists("front/chat.html"):
    shutil.copy("front/chat.html", "front/chat.html.modalbak")
    print("backup: front/chat.html.modalbak")
    print()

import re, sys

path = "front/chat.html"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")

eol = "\r\n" if "\r\n" in c else "\n"

if "settings-modal MOBILE" in c:
    print("Ja aplicado"); sys.exit(0)

# Ancora: fim do bloco .settings-tab-btn.active::before
anchor = """        .settings-tab-btn.active::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 24px;
            border-radius: 0 4px 4px 0;
            background: linear-gradient(180deg, #B349F5, #34D7DD);
        }""".replace("\n", eol)

if c.count(anchor) != 1:
    print("FALHOU: ancora nao encontrada"); sys.exit(1)

css = """

        /* ============ settings-modal MOBILE ============ */
        /* No celular a sidebar (200px fixos) espremia o conteudo.
           Aqui empilhamos: abas horizontais em cima, conteudo embaixo. */
        @media (max-width: 768px) {
            .settings-modal {
                width: 100%;
                max-width: 96vw;
                max-height: 88vh;
                flex-direction: column;
            }

            .settings-sidebar {
                width: 100%;
                flex-direction: row;
                align-items: center;
                gap: 2px;
                padding: 10px 8px;
                border-right: none;
                border-bottom: 1px solid #1e1e22;
                overflow-x: auto;
                overflow-y: hidden;
                flex-shrink: 0;
                scrollbar-width: none;
            }

            .settings-sidebar::-webkit-scrollbar {
                display: none;
            }

            /* Titulo "Configuracoes" some no mobile (economiza espaco) */
            .settings-sidebar > .px-5.mb-6 {
                display: none;
            }

            .settings-tab-btn {
                width: auto;
                flex-shrink: 0;
                padding: 8px 12px;
                font-size: 12px;
                gap: 6px;
                border-radius: 8px;
                white-space: nowrap;
            }

            /* Barra de destaque vira embaixo, nao na lateral */
            .settings-tab-btn.active::before {
                left: 10%;
                right: 10%;
                top: auto;
                bottom: 0;
                transform: none;
                width: auto;
                height: 2px;
                border-radius: 2px 2px 0 0;
                background: linear-gradient(90deg, #B349F5, #34D7DD);
            }

            /* Botao Salvar: sai da sidebar e vira barra fixa embaixo */
            .settings-sidebar > .flex-1 {
                display: none;
            }

            .settings-sidebar > .px-5.mt-4 {
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                margin: 0;
                padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
                background: #0c0c0f;
                border-top: 1px solid #1e1e22;
                z-index: 20;
            }

            /* Espaco para a barra do Salvar nao cobrir o conteudo */
            .settings-content,
            .settings-panel {
                padding-bottom: 76px;
            }
        }""".replace("\n", eol)

c = c.replace(anchor, anchor + css, 1)

with open(path, "wb") as f:
    f.write(c.encode("utf-8"))

print("OK - modal de configuracoes responsivo no mobile")
print()
print("Mudancas (so em telas <= 768px):")
print("  - modal usa 96% da largura (era 92vw com sidebar fixa de 200px)")
print("  - sidebar vira abas HORIZONTAIS no topo (com scroll lateral)")
print("  - conteudo ganha a largura inteira embaixo")
print("  - botao Salvar vira barra fixa na base")
print("  - desktop INALTERADO")
