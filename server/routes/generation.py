import asyncio
import base64
import json
import re
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from google.genai import types

from config import (
    client, MODEL_NAME, GENERATION_CONFIG, MIN_ACCEPTABLE_LENGTH,
    SYSTEM_PROMPT, DEV_MODE, claude_client, CLAUDE_MODEL, DB_NAME
)
from database import validate_user, check_credit_availability, consume_credit
from models import GenerationRequest, PlanRequest, ExtractionRequest
from security import limiter, verify_firebase_token

# Modelos premium custam mais credito e exigem plano Pro/Ultra.
# ANTES: essa regra so era aplicada em /api/confirm-render (depois da geracao
# ja ter acontecido e custado dinheiro de API). Agora e aplicada ANTES de gerar.
PREMIUM_MODELS = {"claude-sonnet", "claude-sonnet-4-6", "gpt4o"}



VISIBILITY_NET = """<script id="aron-visibility-net">
setTimeout(function(){
  document.querySelectorAll('body *').forEach(function(el){
    var cs = getComputedStyle(el);
    if (cs.opacity === '0' && !el.closest('[class*=mobile-nav]') && !el.closest('[id*=menu]')) {
      el.style.opacity = '1';
      el.style.transform = 'none';
      el.style.visibility = 'visible';
    }
  });
}, 2500);
</script>"""

def _inject_visibility_net(html: str) -> str:
    if "</body>" in html:
        return html.replace("</body>", VISIBILITY_NET + "</body>", 1)
    return html + VISIBILITY_NET

GAME_MODE_INSTRUCTION = """

===========================================================
>>> MODO ATIVO: JOGO -- ISTO SOBRESCREVE AS REGRAS DE SITE (1-21)
===========================================================

O usuario quer um JOGO FUNCIONAL DE VERDADE, nao um site que fala sobre um jogo. As regras de layout institucional (REGRA 1 a 21: navbar com Inicio/Sobre/Contato, footer com colunas de links, secao hero com CTA, depoimentos, precos, FAQ) NAO SE APLICAM AQUI. Ignore-as completamente.

PROIBIDO gerar:
- Navbar/menu de navegacao de site
- Footer com colunas de links, redes sociais, copyright de empresa
- Secao "Sobre", "Depoimentos", "Precos", "FAQ", "Contato"
- Qualquer coisa que pareca um site institucional em volta do jogo

OBRIGATORIO gerar:
- Tela cheia (100vw/100vh) dedicada ao jogo
- Cabecalho minimo opcional so com titulo do jogo + pontuacao atual/recorde
- O tabuleiro/area de jogo ocupando o centro, com controles do PROPRIO jogo (reiniciar, novo jogo, pausar) -- nunca links de navegacao
- Aplicar a REGRA 22 com logica JavaScript REAL: estado em variaveis/array, addEventListener nos elementos interativos, funcao que verifica vitoria/derrota/empate, re-renderizacao apos cada jogada
- Teste mental obrigatorio antes de finalizar: "se o usuario clicar numa celula/botao, o estado realmente muda e a tela realmente atualiza?" Se a resposta for nao, o jogo esta incompleto -- corrija antes de entregar.
"""

APP_MODE_INSTRUCTION = """

===========================================================
>>> MODO ATIVO: APP FUNCIONAL -- ISTO SOBRESCREVE AS REGRAS DE SITE (1-21)
===========================================================

O usuario quer um APLICATIVO FUNCIONAL DE VERDADE (CRUD), nao uma pagina institucional bonita sem funcao. As regras de site (navbar de paginas, footer institucional, hero com CTA de marketing, depoimentos, precos, FAQ) NAO SE APLICAM AQUI.

PROIBIDO gerar:
- Navbar de navegacao entre paginas de site
- Footer institucional com colunas de links e copyright de empresa
- Secoes de marketing (hero de vendas, depoimentos, precos, FAQ)

OBRIGATORIO gerar:
- Interface do proprio aplicativo: cabecalho simples com nome do app, area principal com a lista/formulario/dashboard
- Aplicar a REGRA 23 com logica JavaScript REAL: adicionar, editar, excluir e listar itens de verdade
- Persistencia via localStorage funcionando (salvar a cada mudanca, carregar ao abrir a pagina)
- Teste mental obrigatorio antes de finalizar: "se o usuario adicionar um item e recarregar a pagina, ele continua la?" Se a resposta for nao, o app esta incompleto -- corrija antes de entregar.
"""

SITE_MODE_INSTRUCTION = """

>>> MODO ATIVO: SITE. Foque nas REGRAS 1-21 (design, copywriting, direcao de arte). Este e um site institucional/comercial, nao precisa de logica de app ou jogo.
"""


def _get_mode_instruction(mode: str) -> str:
    # Retorna instrucao adicional no topo do prompt conforme o modo escolhido no frontend.
    print(f">>> [MODE] Modo recebido do frontend: '{mode}'")
    if mode == "game":
        return GAME_MODE_INSTRUCTION
    if mode == "app":
        return APP_MODE_INSTRUCTION
    if mode == "site":
        return SITE_MODE_INSTRUCTION
    return ""
def _inject_color_fallbacks(html: str) -> str:
    all_classes = ' '.join(re.findall(r'class="([^"]*)"', html))
    css_rules = set()
    for m in re.finditer(r'bg-\[#([0-9a-fA-F]{3,6})\]', all_classes):
        h = m.group(1)
        css_rules.add(f'.bg-\\[\\#{h}\\]{{background-color:#{h}!important}}')
    for m in re.finditer(r'text-\[#([0-9a-fA-F]{3,6})\]', all_classes):
        h = m.group(1)
        css_rules.add(f'.text-\\[\\#{h}\\]{{color:#{h}!important}}')
    for m in re.finditer(r'border-\[#([0-9a-fA-F]{3,6})\]', all_classes):
        h = m.group(1)
        css_rules.add(f'.border-\\[\\#{h}\\]{{border-color:#{h}!important}}')
    rgba_pats = re.findall(r"rgba\([^)]+\)", all_classes)
    base_rules = """
.bg-primary{background-color:#6366f1!important}
.bg-surface,.bg-surface-950{background-color:#080810!important}
.bg-surface-900{background-color:#0f0f1a!important}
.bg-surface-800{background-color:#13131f!important}
.bg-card{background-color:#13131f!important}
.text-primary{color:#6366f1!important}
.text-surface-400{color:rgba(241,245,249,0.5)!important}
.text-surface-500{color:rgba(241,245,249,0.35)!important}
.border-surface-700{border-color:rgba(255,255,255,0.1)!important}
.border-surface-800{border-color:rgba(255,255,255,0.07)!important}
"""
    css = '<style id="cf">' + base_rules + '\n'.join(css_rules) + '</style>'
    scrollbar_css = '''<style id="sb">
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(128,128,128,0.35);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(128,128,128,0.55)}
html{scrollbar-width:thin;scrollbar-color:rgba(128,128,128,0.35) transparent}
</style>'''
    if '<head>' in html:
        return html.replace('<head>', '<head>\n' + scrollbar_css + '\n' + css, 1)
    return scrollbar_css + css + html


router = APIRouter()

async def _generate_handler(request: Request, body: GenerationRequest, verified_uid: str):
    if DEV_MODE:
        await validate_user(body.user_id)
    else:
        if verified_uid != body.user_id:
            raise HTTPException(
                status_code=403,
                detail="user_id no body nao confere com o token autenticado."
            )

    model_alias = getattr(body, 'model_alias', 'gemini')
    credit_cost = 3 if model_alias in PREMIUM_MODELS else 1

    # Bloquear modelos premium para plano Free/Starter ANTES de gastar tokens de API.
    if model_alias in PREMIUM_MODELS:
        async with aiosqlite.connect(DB_NAME) as db_check:
            async with db_check.execute(
                "SELECT plan FROM users WHERE id = ?", (body.user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                user_plan = row[0] if row else "free"
        if user_plan in ("free", "starter"):
            raise HTTPException(
                status_code=403,
                detail="Modelo premium disponivel apenas nos planos Pro e Ultra. Upgrade necessario!"
            )

    if not await check_credit_availability(body.user_id, credit_cost):
        raise HTTPException(status_code=403, detail="Saldo insuficiente. Adquira mais creditos para continuar.")

    async def event_stream():
        full_text = ""
        try:
            yield f'data: {json.dumps({"type": "start"})}\n\n'

            mode_instruction = _get_mode_instruction(body.mode)

            # ── CONTEXTO: buscar o site ja gerado (modificacao incremental) ──
            html_existente = ""
            try:
                async with aiosqlite.connect(DB_NAME) as _db_ctx:
                    async with _db_ctx.execute(
                        "SELECT full_code FROM chats WHERE id = ? AND user_id = ?",
                        (body.chat_id, body.user_id)
                    ) as _cur:
                        _row = await _cur.fetchone()
                if _row and _row[0]:
                    _raw = _row[0]
                    try:
                        _parsed = json.loads(_raw)
                        html_existente = (_parsed.get("project_structure", {}) or {}).get("html", "") or ""
                    except Exception:
                        html_existente = _raw if _raw.strip().startswith("<") else ""
            except Exception as _e_ctx:
                print(f">>> [CONTEXTO] Falha ao buscar html existente: {_e_ctx}")
                html_existente = ""

            if html_existente and len(html_existente) > 200:
                MAX_CTX = 60000
                _html_ctx = html_existente[:MAX_CTX]
                print(f">>> [CONTEXTO] Modificacao incremental — html atual: {len(html_existente)} chars")
                full_prompt = (
                    f"{SYSTEM_PROMPT}{mode_instruction}\n\n"
                    "=== MODO EDICAO (NAO CRIE UM SITE NOVO) ===\n"
                    "O usuario JA TEM um projeto pronto. O codigo COMPLETO dele esta abaixo.\n"
                    "Sua tarefa e APLICAR SOMENTE a alteracao pedida, preservando TODO o resto.\n\n"
                    "REGRAS OBRIGATORIAS DE EDICAO:\n"
                    "1. NAO recrie o site do zero. NAO invente novas secoes que nao foram pedidas.\n"
                    "2. PRESERVE exatamente: paleta de cores, fontes, textos, layout, secoes e animacoes existentes.\n"
                    "3. Altere APENAS o que o usuario pediu no PEDIDO abaixo.\n"
                    "4. Retorne o HTML COMPLETO e final (do <!DOCTYPE html> ate </html>), ja com a alteracao aplicada.\n"
                    "5. Se o pedido for ambiguo, faca a mudanca minima e segura.\n\n"
                    "--- CODIGO ATUAL DO PROJETO ---\n"
                    f"{_html_ctx}\n"
                    "--- FIM DO CODIGO ATUAL ---\n\n"
                    f"--- ALTERACAO PEDIDA PELO USUARIO ---\n{body.prompt}"
                )
            else:
                full_prompt = f"{SYSTEM_PROMPT}{mode_instruction}\n\n--- PEDIDO DO USUARIO ---\n{body.prompt}"
            # model_alias e credit_cost ja foram calculados e validados antes do stream comecar

            # Processar imagem de referencia (se houver)
            clone_instr = ""
            img_b64 = None
            mime = "image/jpeg"
            if getattr(body, 'image_data', None):
                clone_instr = (
                    "TAREFA CRITICA: CLONAGEM VISUAL EXATA DA IMAGEM DE REFERENCIA ANEXADA.\n"
                    "Analise cada detalhe da imagem e recrie em HTML+CSS identico ao original.\n"
                    "REGRAS OBRIGATORIAS:\n"
                    "1. CORES DE FUNDO: extraia e use o hexadecimal EXATO do fundo da pagina e de cada secao.\n"
                    "2. CORES DE TEXTO: se algum texto tem cor diferente do preto/branco (ex: verde, azul, gradiente), "
                    "replique essa cor EXATAMENTE. Textos coloridos sao um elemento de design critico.\n"
                    "3. TEXTOS: reproduza EXATAMENTE o texto visivel, palavra por palavra, no mesmo tamanho e peso.\n"
                    "4. LAYOUT: replique a estrutura na MESMA ordem e posicionamento (colunas, grid, alinhamento).\n"
                    "5. IMAGENS: para cada imagem ou foto na referencia, use esta URL confiavel: "
                    "https://picsum.photos/seed/[palavra-tema]/800/600 "
                    "onde [palavra-tema] e uma palavra em ingles que descreve o conteudo (ex: food, nature, product). "
                    "NUNCA use source.unsplash.com pois esta fora do ar.\n"
                    "6. BOTOES: replique cor, formato (arredondado/quadrado), tamanho e texto dos botoes.\n"
                    "7. ESPACAMENTO: respeite proporcoes, padding e margens visiveis na imagem.\n"
                    "PROIBIDO: inventar cores, mudar textos, reordenar secoes, usar URLs de imagem que nao sejam picsum.photos.\n\n"
                )
                full_prompt = clone_instr + full_prompt
                img_str = body.image_data
                if ',' in img_str:
                    header_part, img_b64 = img_str.split(',', 1)
                    mime = header_part.split(':')[1].split(';')[0] if ':' in header_part else 'image/jpeg'
                else:
                    img_b64, mime = img_str, 'image/jpeg'

            # ── Roteamento por modelo ──────────────────────────────
            if model_alias.startswith('claude') and claude_client:
                # Claude Sonnet — streaming via SDK Anthropic
                user_content = f"--- PEDIDO DO USUARIO ---\n{body.prompt}"
                if clone_instr:
                    user_content = clone_instr + user_content
                if img_b64:
                    claude_content = [
                        {"type": "image", "source": {"type": "base64", "media_type": mime, "data": img_b64}},
                        {"type": "text", "text": user_content}
                    ]
                else:
                    claude_content = [{"type": "text", "text": user_content}]

                async with claude_client.messages.stream(
                    model=CLAUDE_MODEL,
                    max_tokens=15000,
                    system=SYSTEM_PROMPT + _get_mode_instruction(body.mode),
                    messages=[{"role": "user", "content": claude_content}]
                ) as stream:
                    async for text in stream.text_stream:
                        full_text += text
                        yield f'data: {json.dumps({"type": "chunk", "text": text})}\n\n'

            else:
                # Gemini — streaming padrao
                if img_b64:
                    img_bytes = base64.b64decode(img_b64)
                    contents = [
                        types.Content(role="user", parts=[
                            types.Part.from_bytes(data=img_bytes, mime_type=mime),
                            types.Part.from_text(text=full_prompt),
                        ])
                    ]
                else:
                    contents = full_prompt

                async for chunk in await client.aio.models.generate_content_stream(
                    model=MODEL_NAME,
                    contents=contents,
                    config=GENERATION_CONFIG,
                ):
                    # Separar partes de pensamento (thought=True) do codigo real
                    for part in chunk.candidates[0].content.parts:
                        if getattr(part, "thought", False) and part.text:
                            yield f'data: {json.dumps({"type": "thought", "text": part.text})}\n\n'
                        elif part.text:
                            full_text += part.text
                            yield f'data: {json.dumps({"type": "chunk", "text": part.text})}\n\n'

            # ── Processar HTML final ───────────────────────────────
            if not full_text or len(full_text) < MIN_ACCEPTABLE_LENGTH:
                yield f'data: {json.dumps({"type": "error", "message": "IA nao gerou conteudo suficiente"})}\n\n'
                return

            raw = full_text.strip()
            if raw.startswith("```"):
                import re as _re
                raw = _re.sub(r"^```(json|html|xml)?\n?", "", raw)
                raw = _re.sub(r"```$", "", raw).strip()

            import re as _re
            html_match = _re.search(r"(<!DOCTYPE html>|<html[\s\S]*?)<\/html>", raw, _re.IGNORECASE)
            if html_match:
                extracted = html_match.group(0)
            else:
                div_match = _re.search(r"(<div|<body|<section|<main)[\s\S]*", raw, _re.IGNORECASE)
                extracted = div_match.group(0) if div_match else raw

            extracted = (extracted
                .replace("\\n", "\n")
                .replace('\\"', '"')
                .replace("\\t", "\t")
                .replace("\\\\", "\\"))

            import base64 as _b64
            extracted = _inject_color_fallbacks(extracted)
            encoded = _b64.b64encode(extracted.encode("utf-8")).decode("utf-8")

            # Debito do credito acontece AQUI, no servidor, logo que a geracao
            # e confirmada valida — nunca depende de uma chamada separada do
            # cliente (isso permitia gerar de graca so ignorando essa chamada).
            debito_ok = await consume_credit(body.user_id, body.chat_id, credit_cost)
            if not debito_ok:
                yield f'data: {json.dumps({"type": "error", "message": "Saldo insuficiente para concluir a geracao."})}\n\n'
                return

            yield f'data: {json.dumps({"type": "done", "html_base64": encoded, "user_id": body.user_id, "chat_id": body.chat_id, "credits_charged": credit_cost})}\n\n'

        except Exception as e:
            import traceback
            print(f">>> [STREAM ERROR] {e}\n{traceback.format_exc()}")
            yield f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/generate/stream")
@limiter.limit("10/minute")
async def generate_stream_endpoint(
    request: Request,
    body: GenerationRequest,
    verified_uid: str = Depends(verify_firebase_token)
):
    return await _generate_handler(request, body, verified_uid)

@router.post("/api/generate")
@limiter.limit("10/minute")
async def generate_api_endpoint(
    request: Request,
    body: GenerationRequest,
    verified_uid: str = Depends(verify_firebase_token)
):
    return await _generate_handler(request, body, verified_uid)

@router.post("/api/confirm-render")
async def confirm_render(request: Request, verified_uid: str = Depends(verify_firebase_token)):
    """
    LEGADO: o debito de credito agora acontece dentro de _generate_handler,
    no exato momento em que a IA termina a geracao com sucesso (ver
    consume_credit logo antes do evento 'done' em /generate/stream).

    Essa rota NAO debita mais credito nenhum — ela existe apenas para nao
    quebrar chamadas do frontend que ainda avisam o backend apos renderizar.
    Mantemos autenticacao + checagem de dono para que ela nao possa ser usada
    por terceiros para consultar/alterar dados de outro usuario.
    """
    try:
        data = await request.json()
    except Exception:
        data = {}

    user_id = data.get("user_id")
    if not DEV_MODE and verified_uid != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    return {"status": "success", "note": "credito ja debitado no momento da geracao"}


def _extract_json(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```"):
        t = t[3:]
        if t[:4].lower() == "json":
            t = t[4:]
        if t.endswith("```"):
            t = t[:-3]
        t = t.strip()
    first_obj = t.find("{")
    first_arr = t.find("[")
    starts = [p for p in (first_obj, first_arr) if p != -1]
    if starts:
        start = min(starts)
        end = max(t.rfind("}"), t.rfind("]"))
        if end > start:
            t = t[start:end + 1]
    return t.strip()


@router.post("/api/plan-project")
@limiter.limit("10/minute")
async def plan_project(request: Request, body: PlanRequest, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != body.user_id:
        raise HTTPException(status_code=403, detail="user_id no body nao confere com o token autenticado.")
    await validate_user(body.user_id)
    if not await check_credit_availability(body.user_id, 1):
        raise HTTPException(status_code=402, detail="Creditos insuficientes")

    system_instruction = """
    Voce e o 'Aron Planner'. Crie um plano estrategico (BluePrint) para o site solicitado.
    Responda APENAS em JSON com:
    {
      "brand_identity": {"name": "...", "voice_tone": "...", "colors": ["#...", "#..."]},
      "sitemap": [{"section": "...", "objective": "..."}],
      "tech_requirements": ["...", "..."],
      "user_flow": ["...", "..."]
    }
    """
    try:
        response = None
        for attempt in range(3):
            try:
                response = await client.aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=f"{system_instruction}\n\nPROMPT: {body.prompt}",
                    config=types.GenerateContentConfig(temperature=0.3)
                )
                break
            except Exception as e:
                print(f">>> [PLAN RETRY {attempt+1}/3] Gemini Error: {str(e)}")
                if attempt == 2:
                    raise e
                await asyncio.sleep(2)

        try:
            raw_text = response.text if response else ""
        except Exception:
            raw_text = ""

        plan_data = _extract_json(raw_text)

        if not plan_data or len(plan_data) < 20:
            raise HTTPException(status_code=502, detail="A IA retornou uma resposta vazia.")

        try:
            parsed = json.loads(plan_data)
        except json.JSONDecodeError as je:
            print(f">>> [PLAN JSON ERROR] {str(je)}")
            raise HTTPException(status_code=502, detail="A IA retornou um JSON invalido.")

        await consume_credit(body.user_id, "plan_project", 1)
        return JSONResponse(content=parsed)

    except HTTPException:
        raise
    except Exception as e:
        print(f">>> [PLAN ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


CLARIFY_INSTRUCTION = (
    "Voce e o Aron Interviewer. Analise o pedido do usuario e decida se tem detalhes "
    "SUFICIENTES para gerar um projeto de qualidade, ou se faltam informacoes criticas.\n\n"
    "REGRAS: Pedidos simples e completos = ready true, nao pergunte nada. "
    "Pedidos vagos ou complexos (um sistema, um app, site pra empresa) = ready false. "
    "Projetos com app/sistema/dashboard/multiusuario quase sempre precisam de perguntas. "
    "Maximo 4 perguntas, priorize as que mais mudam o resultado. "
    "Cada pergunta e tipo botoes (multipla escolha) ou texto (livre).\n\n"
    "TIPOS UTEIS: autenticacao (Sim/Nao), paleta de cores (opcoes), estilo visual "
    "(minimalista/moderno/corporativo/colorido), publico-alvo (texto), funcionalidades (texto).\n\n"
    "Responda APENAS JSON sem markdown sem crases. Formato: "
    '{"ready": false, "questions": ['
    '{"id": "auth", "pergunta": "Seu sistema vai ter login e cadastro?", "tipo": "botoes", "opcoes": ["Sim, com autenticacao", "Nao, acesso livre", "Nao sei"]}, '
    '{"id": "cores", "pergunta": "Qual paleta de cores?", "tipo": "botoes", "opcoes": ["Azul e roxo", "Verde e preto", "Tons quentes", "Deixa a IA escolher"]}, '
    '{"id": "publico", "pergunta": "Quem vai usar esse projeto?", "tipo": "texto", "opcoes": []}'
    ']}'
    ". Se o pedido ja for suficiente responda apenas: "
    '{"ready": true, "questions": []}'
)


@router.post("/api/clarify")
@limiter.limit("15/minute")
async def clarify_project(request: Request, body: PlanRequest, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != body.user_id:
        raise HTTPException(status_code=403, detail="user_id no body nao confere com o token autenticado.")
    await validate_user(body.user_id)

    try:
        response = None
        MAX_TENTATIVAS = 2
        for attempt in range(MAX_TENTATIVAS):
            try:
                # thinking_budget=0: o clarify so decide se pergunta algo — nao precisa
                # "pensar". Com thinking levava ~8s; sem, cai para ~2.5s.
                _cfg_clarify = types.GenerateContentConfig(
                    max_output_tokens=900,
                    temperature=0.2,
                )
                try:
                    _cfg_clarify.thinking_config = types.ThinkingConfig(thinking_budget=0)
                except Exception:
                    pass

                response = await client.aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=f"{CLARIFY_INSTRUCTION}\n\nPEDIDO DO USUARIO: {body.prompt}",
                    config=_cfg_clarify
                )
                break
            except Exception as e:
                err = str(e)
                is_503 = "503" in err or "UNAVAILABLE" in err or "high demand" in err
                print(f">>> [CLARIFY RETRY {attempt+1}/{MAX_TENTATIVAS}] {'503 sobrecarga' if is_503 else err[:80]}")
                if attempt == MAX_TENTATIVAS - 1:
                    raise e
                await asyncio.sleep(2 if is_503 else 1)

        try:
            raw_text = response.text if response else ""
        except Exception:
            raw_text = ""

        clarify_data = _extract_json(raw_text)
        if not clarify_data:
            print(">>> [CLARIFY] Sem JSON, liberando geracao direta")
            return JSONResponse(content={"ready": True, "questions": []})

        try:
            parsed = json.loads(clarify_data)
        except json.JSONDecodeError:
            print(">>> [CLARIFY JSON ERROR] liberando geracao direta")
            return JSONResponse(content={"ready": True, "questions": []})

        if not isinstance(parsed, dict):
            return JSONResponse(content={"ready": True, "questions": []})
        if parsed.get("ready") is True:
            return JSONResponse(content={"ready": True, "questions": []})

        questions = parsed.get("questions", [])
        if not isinstance(questions, list) or len(questions) == 0:
            return JSONResponse(content={"ready": True, "questions": []})

        parsed["questions"] = questions[:4]
        parsed["ready"] = False
        return JSONResponse(content=parsed)

    except HTTPException:
        raise
    except Exception as e:
        print(f">>> [CLARIFY ERROR] {str(e)}")
        return JSONResponse(content={"ready": True, "questions": []})


@router.post("/api/extract-components")
@limiter.limit("10/minute")
async def extract_components(request: Request, body: ExtractionRequest, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != body.user_id:
        raise HTTPException(status_code=403, detail="user_id no body nao confere com o token autenticado.")
    await validate_user(body.user_id)

    system_instruction = """
    Analise o HTML e extraia os principais componentes UI de alto nivel
    (Navbar, Hero, Features, Pricing, CTA, Footer, Depoimentos, etc).
    Responda APENAS com um array JSON valido, sem nenhum texto fora dele,
    no formato exato:
    [
      {"tipo": "Navbar", "id": "nav-1", "preview_text": "Resumo curto do bloco", "outerHTML": "<nav>...</nav>"}
    ]
    Regras:
    - "tipo": nome do componente
    - "id": identificador curto e unico (ex: hero-1, cta-1, footer-1)
    - "preview_text": resumo de 1 linha do conteudo do bloco
    - "outerHTML": o HTML COMPLETO e valido daquele bloco
    Extraia no maximo os 8 blocos principais para nao truncar.
    """
    try:
        response = None
        for attempt in range(3):
            try:
                response = await client.aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=f"{system_instruction}\n\nHTML: {body.html}",
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                break
            except Exception as e:
                print(f">>> [EXTRACT RETRY {attempt+1}/3] Gemini Error: {str(e)}")
                if attempt == 2:
                    raise e
                await asyncio.sleep(2)

        components_data = _extract_json(response.text if response else "")
        if components_data and len(components_data) > 5:
            try:
                return JSONResponse(content=json.loads(components_data))
            except json.JSONDecodeError:
                return JSONResponse(content=[])
        else:
            return JSONResponse(content=[])
    except Exception:
        return JSONResponse(content=[])
