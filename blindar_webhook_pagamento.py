# BLINDAGEM DO WEBHOOK DE PAGAMENTO (dinheiro real)
# Corrige: falha aberta sem secret, modo mock creditando de graca,
# erros silenciados que perdiam creditos, falta de validacao de valor,
# credito para usuario inexistente e idempotencia fragil.
# Faz backup automatico antes de alterar.
import shutil, os
if os.path.exists("server/payments.py"):
    shutil.copy("server/payments.py", "server/payments.py.bak")
    print("backup salvo: server/payments.py.bak")

import ast, sys

path = "server/payments.py"
with open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

eol = "\r\n" if "\r\n" in content else "\n"

# Localizar o inicio do webhook e substituir a funcao inteira
inicio = content.find('@router.post("/webhook")')
if inicio == -1:
    print("FALHOU: webhook nao encontrado"); sys.exit(1)

# O webhook vai ate o fim do arquivo (e a ultima funcao)
antes = content[:inicio]

novo_webhook = '''@router.post("/webhook")
async def mp_webhook(request: Request, x_signature: Optional[str] = Header(None), x_request_id: Optional[str] = Header(None)):
    """
    Webhook do Mercado Pago. Regras de ouro (dinheiro real):
      - Falha FECHADA: sem secret ou sem token -> rejeita (nunca credita "no escuro").
      - Idempotencia: marca o payment_id ANTES de creditar, na mesma transacao.
      - Valida o valor pago contra o preco do plano.
      - Erros retornam 500 para o MP REENVIAR (nunca "ok" mentiroso).
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    action = request.query_params.get("action") or request.query_params.get("topic") or body.get("action")
    payment_id = request.query_params.get("data.id") or request.query_params.get("id")
    if not payment_id and "data" in body:
        payment_id = body.get("data", {}).get("id")
    if not payment_id or action not in ("payment.created", "payment.updated"):
        return {"status": "ignored"}

    # ---- 1. SEGURANCA: assinatura obrigatoria (falha fechada) ----
    secret = os.getenv("MP_WEBHOOK_SECRET")
    if not secret:
        print(">>> [WEBHOOK][BLOQUEADO] MP_WEBHOOK_SECRET ausente. Nenhum credito concedido.")
        raise HTTPException(status_code=503, detail="Webhook nao configurado")
    if not x_signature:
        raise HTTPException(status_code=403, detail="Assinatura ausente no webhook")
    parts = dict(p.split("=", 1) for p in x_signature.split(",") if "=" in p)
    ts, v1 = parts.get("ts", "").strip(), parts.get("v1", "").strip()
    if not ts or not v1:
        raise HTTPException(status_code=403, detail="Formato de assinatura invalido")
    manifest = f"id:{payment_id};request-id:{x_request_id};ts:{ts};"
    hmac_calc = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(hmac_calc, v1):
        print(f">>> [WEBHOOK][BLOQUEADO] Assinatura invalida para payment {payment_id}")
        raise HTTPException(status_code=403, detail="Assinatura invalida")

    # ---- 2. Token obrigatorio (sem modo mock creditando de graca) ----
    if not os.getenv("MP_ACCESS_TOKEN"):
        print(">>> [WEBHOOK][BLOQUEADO] MP_ACCESS_TOKEN ausente. Nenhum credito concedido.")
        raise HTTPException(status_code=503, detail="Pagamentos nao configurados")

    p_id = str(payment_id)

    try:
        # ---- 3. Consultar o pagamento NA FONTE (nunca confiar no corpo do webhook) ----
        mp = get_mp_client()
        info = mp.payment().get(payment_id)
        if info.get("status") != 200:
            print(f">>> [WEBHOOK] Falha ao consultar payment {p_id} no MP")
            raise HTTPException(status_code=500, detail="Falha ao consultar pagamento")

        pdata = info.get("response", {}) or {}
        if pdata.get("status") != "approved":
            return {"status": "not_approved", "mp_status": pdata.get("status")}

        meta = pdata.get("metadata") or {}
        user_id = meta.get("user_id")
        plan_id = meta.get("plan_id", "")
        plan = PLANS.get(plan_id)

        if not user_id or not plan:
            print(f">>> [WEBHOOK][ALERTA] payment {p_id} aprovado sem metadata valido: {meta}")
            raise HTTPException(status_code=500, detail="Metadata invalido")

        # ---- 4. Validar o VALOR realmente pago contra o preco do plano ----
        pago = float(pdata.get("transaction_amount") or 0)
        esperado = float(plan["price"])
        if abs(pago - esperado) > 0.01:
            print(f">>> [WEBHOOK][FRAUDE?] payment {p_id}: pago R${pago} != plano {plan_id} R${esperado}. NAO creditado.")
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO processed_payments (payment_id, processed_at) VALUES (?, CURRENT_TIMESTAMP)",
                    (p_id,))
                await db.execute("UPDATE payment_attempts SET status = 'valor_divergente' WHERE payment_id = ?", (p_id,))
                await db.commit()
            return {"status": "amount_mismatch"}

        credits_to_add = int(plan["credits"])
        plan_tier = plan["title"].lower()

        # ---- 5. Creditar de forma atomica e idempotente ----
        async with aiosqlite.connect(DB_NAME) as db:
            # Idempotencia: se ja existir, o INSERT falha e nao credita de novo
            cur = await db.execute(
                "INSERT OR IGNORE INTO processed_payments (payment_id, processed_at) VALUES (?, CURRENT_TIMESTAMP)",
                (p_id,))
            if cur.rowcount == 0:
                await db.commit()
                print(f">>> [WEBHOOK] payment {p_id} ja processado antes. Ignorando (idempotente).")
                return {"status": "already_processed"}

            # Garantir que o usuario existe ANTES de creditar
            async with db.execute("SELECT credits FROM users WHERE id = ?", (user_id,)) as c2:
                urow = await c2.fetchone()
            if not urow:
                await db.rollback()
                print(f">>> [WEBHOOK][ERRO] user_id {user_id} nao existe. Payment {p_id} NAO processado (MP vai reenviar).")
                raise HTTPException(status_code=500, detail="Usuario nao encontrado")

            saldo_antes = urow[0] or 0

            await db.execute("UPDATE users SET credits = credits + ?, plan = ? WHERE id = ?",
                             (credits_to_add, plan_tier, user_id))
            await db.execute("UPDATE payment_attempts SET status = 'approved' WHERE payment_id = ?", (p_id,))

            # Log de auditoria (best-effort: nao derruba o credito se a tabela divergir)
            try:
                await db.execute(
                    "INSERT INTO credit_logs (user_id, amount, reason, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                    (user_id, credits_to_add, f"pagamento {p_id} plano {plan_id}"))
            except Exception as _e_log:
                print(f">>> [WEBHOOK] (aviso) credit_logs nao registrado: {_e_log}")

            await db.commit()

        print(f">>> [PAYMENT][OK] +{credits_to_add} creditos para {user_id} "
              f"(saldo {saldo_antes} -> {saldo_antes + credits_to_add}) | plano {plan_tier} | payment {p_id}")
        return {"status": "success", "credits_added": credits_to_add, "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        # NUNCA devolver "ok" em caso de erro: o MP precisa reenviar o webhook
        print(f">>> [WEBHOOK][ERRO CRITICO] payment {p_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar webhook")
'''

novo_webhook = novo_webhook.replace("\n", eol)
content = antes + novo_webhook

try:
    ast.parse(content)
except SyntaxError as e:
    print("ERRO DE SINTAXE:", e)
    sys.exit(1)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)
print("OK - webhook blindado")
print("Sintaxe Python: valida")
