import os
import aiosqlite
import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel
import mercadopago
from typing import Optional

from config import DB_NAME
from security import verify_firebase_token, DEV_MODE

router = APIRouter()

class PixCreateRequest(BaseModel):
    plan_id: str
    user_id: str

PLANS = {
    "PLAN_STARTER": {"title": "Starter", "price": 29.90, "credits": 50},
    "PLAN_PRO":     {"title": "Pro",     "price": 59.90, "credits": 150},
    "PLAN_ULTRA":   {"title": "Ultra",   "price": 99.90, "credits": 350},
}

def get_mp_client():
    token = os.getenv("MP_ACCESS_TOKEN")
    return mercadopago.SDK(token if token else "TEST-TOKEN")

@router.post("/create")
async def create_pix_payment(request: PixCreateRequest, x_idempotency_key: Optional[str] = Header(None), verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != request.user_id:
        raise HTTPException(status_code=403, detail="user_id no body nao confere com o token autenticado.")
    if request.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Plano invalido")
    plan = PLANS[request.plan_id]
    user_email = "unknown@email.com"
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT email FROM users WHERE id = ?", (request.user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                user_email = row[0]
    if not os.getenv("MP_ACCESS_TOKEN"):
        mock_id = "mock_" + os.urandom(4).hex()
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO payment_attempts (payment_id, user_id, user_email, status, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (mock_id, request.user_id, user_email, "pending"))
            await db.commit()
        return {"qr_code_64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==", "qr_code": "mock-pix-code", "payment_id": mock_id}
    mp = get_mp_client()
    payment_data = {"transaction_amount": float(plan["price"]), "description": f"Aron Studio - {plan['title']}", "payment_method_id": "pix", "payer": {"email": user_email}, "metadata": {"user_id": request.user_id, "plan_id": request.plan_id}}
    request_options = mercadopago.config.RequestOptions()
    if x_idempotency_key:
        request_options.custom_headers = {"x-idempotency-key": x_idempotency_key}
    try:
        resp = mp.payment().create(payment_data, request_options)
        data = resp.get("response", {})
        if "id" not in data:
            raise Exception(f"Falha MP: {resp}")
        payment_id = str(data["id"])
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO payment_attempts (payment_id, user_id, user_email, status, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (payment_id, request.user_id, user_email, "pending"))
            await db.commit()
        return {"qr_code_64": data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", ""), "qr_code": data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", ""), "payment_id": payment_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{payment_id}")
async def get_payment_status(payment_id: str, verified_uid: str = Depends(verify_firebase_token)):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT status, user_id FROM payment_attempts WHERE payment_id = ?", (payment_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"status": "not_found"}
            if not DEV_MODE and row[1] != verified_uid:
                raise HTTPException(status_code=403, detail="Acesso negado")
            return {"status": row[0]}



class ProcessPaymentRequest(BaseModel):
    plan_id: str
    user_id: str
    formData: dict

@router.post("/process")
async def process_payment(request: ProcessPaymentRequest, verified_uid: str = Depends(verify_firebase_token)):
    """Processa o pagamento do Payment Brick (PIX, cartao, boleto)."""
    if not DEV_MODE and verified_uid != request.user_id:
        raise HTTPException(status_code=403, detail="user_id no body nao confere com o token autenticado.")
    if request.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Plano invalido")
    plan = PLANS[request.plan_id]
    mp = get_mp_client()

    payment_data = dict(request.formData)
    payment_data["transaction_amount"] = float(plan["price"])
    payment_data["description"] = f"Aron Elite V1 - {plan['title']}"
    payment_data["metadata"] = {"user_id": request.user_id, "plan_id": request.plan_id}
    payment_data.setdefault("payer", {})

    try:
        result = mp.payment().create(payment_data)
        resp = result.get("response", {})
        status = resp.get("status")
        p_id = resp.get("id")

        # Registrar tentativa
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT OR REPLACE INTO payment_attempts (payment_id, user_id, plan_id, status) VALUES (?, ?, ?, ?)",
                (str(p_id), request.user_id, request.plan_id, status or "pending"),
            )
            await db.commit()

        out = {"status": status, "payment_id": p_id, "status_detail": resp.get("status_detail")}

        # PIX: devolver QR Code
        poi = resp.get("point_of_interaction") or {}
        tdata = poi.get("transaction_data") or {}
        if tdata.get("qr_code"):
            out["qr_code"] = tdata.get("qr_code")
            out["qr_code_base64"] = tdata.get("qr_code_base64")
            out["ticket_url"] = tdata.get("ticket_url")

        # Boleto
        tdetails = resp.get("transaction_details") or {}
        if tdetails.get("external_resource_url"):
            out["boleto_url"] = tdetails.get("external_resource_url")

        return out
    except Exception as e:
        print(f">>> [PAYMENT] Erro ao processar: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar pagamento")

class PreferenceRequest(BaseModel):
    plan_id: str
    user_id: str

@router.post("/preference")
async def create_preference(request: PreferenceRequest, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != request.user_id:
        raise HTTPException(status_code=403, detail="user_id no body nao confere com o token autenticado.")
    if request.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Plano invalido")
    plan = PLANS[request.plan_id]
    user_email = "pagador@email.com"
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT email FROM users WHERE id = ?", (request.user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                user_email = row[0]
    if not os.getenv("MP_ACCESS_TOKEN"):
        mock_id = "mock_pref_" + os.urandom(4).hex()
        return {"preference_id": mock_id, "init_point": f"https://www.mercadopago.com.br/checkout/v1/redirect?pref_id={mock_id}"}
    mp = get_mp_client()
    pref_data = {"items": [{"title": f"Aron Studio - {plan['title']}", "quantity": 1, "unit_price": float(plan["price"]), "currency_id": "BRL"}], "payer": {"email": user_email}, "payment_methods": {"installments": 12}, "back_urls": {"success": "/checkout?status=success", "failure": "/checkout?status=failure", "pending": "/checkout?status=pending"}, "auto_return": "approved", "metadata": {"user_id": request.user_id, "plan_id": request.plan_id}}
    try:
        result = mp.preference().create(pref_data)
        data = result.get("response", {})
        if "id" not in data:
            raise HTTPException(status_code=500, detail="Falha ao criar preferencia MP")
        return {"preference_id": data["id"], "init_point": data.get("init_point", "")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
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
