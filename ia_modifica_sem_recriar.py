# Faz a IA reconhecer o site ja gerado e SO ajustar o que o usuario pedir
import ast, sys

path = "server/routes/generation.py"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

eol = "\r\n" if "\r\n" in content else "\n"

old = (
    "            mode_instruction = _get_mode_instruction(body.mode)" + eol +
    "            full_prompt = f\"{SYSTEM_PROMPT}{mode_instruction}\\n\\n--- PEDIDO DO USUARIO ---\\n{body.prompt}\"" + eol
)

new = (
    "            mode_instruction = _get_mode_instruction(body.mode)" + eol +
    eol +
    "            # ── CONTEXTO: buscar o site ja gerado (modificacao incremental) ──" + eol +
    "            html_existente = \"\"" + eol +
    "            try:" + eol +
    "                async with aiosqlite.connect(DB_NAME) as _db_ctx:" + eol +
    "                    async with _db_ctx.execute(" + eol +
    "                        \"SELECT full_code FROM chats WHERE id = ? AND user_id = ?\"," + eol +
    "                        (body.chat_id, body.user_id)" + eol +
    "                    ) as _cur:" + eol +
    "                        _row = await _cur.fetchone()" + eol +
    "                if _row and _row[0]:" + eol +
    "                    _raw = _row[0]" + eol +
    "                    try:" + eol +
    "                        _parsed = json.loads(_raw)" + eol +
    "                        html_existente = (_parsed.get(\"project_structure\", {}) or {}).get(\"html\", \"\") or \"\"" + eol +
    "                    except Exception:" + eol +
    "                        html_existente = _raw if _raw.strip().startswith(\"<\") else \"\"" + eol +
    "            except Exception as _e_ctx:" + eol +
    "                print(f\">>> [CONTEXTO] Falha ao buscar html existente: {_e_ctx}\")" + eol +
    "                html_existente = \"\"" + eol +
    eol +
    "            if html_existente and len(html_existente) > 200:" + eol +
    "                MAX_CTX = 60000" + eol +
    "                _html_ctx = html_existente[:MAX_CTX]" + eol +
    "                print(f\">>> [CONTEXTO] Modificacao incremental — html atual: {len(html_existente)} chars\")" + eol +
    "                full_prompt = (" + eol +
    "                    f\"{SYSTEM_PROMPT}{mode_instruction}\\n\\n\"" + eol +
    "                    \"=== MODO EDICAO (NAO CRIE UM SITE NOVO) ===\\n\"" + eol +
    "                    \"O usuario JA TEM um projeto pronto. O codigo COMPLETO dele esta abaixo.\\n\"" + eol +
    "                    \"Sua tarefa e APLICAR SOMENTE a alteracao pedida, preservando TODO o resto.\\n\\n\"" + eol +
    "                    \"REGRAS OBRIGATORIAS DE EDICAO:\\n\"" + eol +
    "                    \"1. NAO recrie o site do zero. NAO invente novas secoes que nao foram pedidas.\\n\"" + eol +
    "                    \"2. PRESERVE exatamente: paleta de cores, fontes, textos, layout, secoes e animacoes existentes.\\n\"" + eol +
    "                    \"3. Altere APENAS o que o usuario pediu no PEDIDO abaixo.\\n\"" + eol +
    "                    \"4. Retorne o HTML COMPLETO e final (do <!DOCTYPE html> ate </html>), ja com a alteracao aplicada.\\n\"" + eol +
    "                    \"5. Se o pedido for ambiguo, faca a mudanca minima e segura.\\n\\n\"" + eol +
    "                    \"--- CODIGO ATUAL DO PROJETO ---\\n\"" + eol +
    "                    f\"{_html_ctx}\\n\"" + eol +
    "                    \"--- FIM DO CODIGO ATUAL ---\\n\\n\"" + eol +
    "                    f\"--- ALTERACAO PEDIDA PELO USUARIO ---\\n{body.prompt}\"" + eol +
    "                )" + eol +
    "            else:" + eol +
    "                full_prompt = f\"{SYSTEM_PROMPT}{mode_instruction}\\n\\n--- PEDIDO DO USUARIO ---\\n{body.prompt}\"" + eol
)

if content.count(old) != 1:
    print("FALHOU: bloco nao encontrado (", content.count(old), ")")
    sys.exit(1)

content = content.replace(old, new, 1)

try:
    ast.parse(content)
except SyntaxError as e:
    print("ERRO DE SINTAXE:", e)
    sys.exit(1)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)
print("OK - contexto do site existente adicionado (modificacao incremental)")
print("Sintaxe Python: valida")
