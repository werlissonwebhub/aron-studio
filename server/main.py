"""
main.py — Ponto de entrada da Aron Studio API

Responsabilidades:
  - Inicializar o app FastAPI com lifespan
  - Registrar middlewares (CORS, timeout, rate limit)
  - Incluir todos os routers
  - Servir o frontend estatico
"""

import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from database import init_db
from security import DEV_MODE, limiter
from payments import router as payments_router
from routes.auth import router as auth_router
from routes.projects import router as projects_router
from routes.generation import router as generation_router
from routes.deploy import router as deploy_router
from routes.prospecting import router as prospecting_router


# =================================================================
# LIFESPAN — startup e shutdown
# =================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(">>> [BOOT] Banco de dados inicializado.")
    yield


# =================================================================
# APP
# =================================================================
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv("ENVIRONMENT", "development"),
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
            LoggingIntegration(level=None, event_level="ERROR"),
        ],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )
    print(">>> [SENTRY] Monitoramento ativado")
else:
    print(">>> [SENTRY] DSN ausente — monitoramento desativado")

app = FastAPI(lifespan=lifespan)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
# allow_origins=["*"] nao pode ser combinado com allow_credentials=True
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if DEV_MODE or not _raw_origins:
    ALLOWED_ORIGINS   = ["*"]
    ALLOW_CREDENTIALS = False
    print(">>> [CORS] DEV_MODE: allow_origins=['*'], credentials=False")
else:
    ALLOWED_ORIGINS   = [o.strip() for o in _raw_origins.split(",") if o.strip()]
    ALLOW_CREDENTIALS = True
    print(f">>> [CORS] Producao: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-Idempotency-Key"],
)

# Timeout global de 180s
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=180.0)
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"detail": "Timeout 180s"})

# Filtra logs de ruido (chrome, json extension requests)
@app.middleware("http")
async def log_filter_middleware(request: Request, call_next):
    path = request.url.path
    if "chrome" in path.lower() or ".json" in path.lower():
        response = await call_next(request)
        if response.status_code == 404:
            return Response(status_code=404)
        return response
    return await call_next(request)

# Handler de validacao (debug 422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    body_bytes = await request.body()
    errors = exc.errors()
    print(f"[VALIDATION ERROR] path={request.url.path} errors={errors}")
    print(f"[VALIDATION ERROR] body (so no log do servidor, nunca na resposta): {body_bytes!r}")

    # Remove o campo 'input' de cada erro antes de responder — ele ecoa de
    # volta o valor que a pessoa enviou (pode conter senha, token, etc).
    safe_errors = [
        {k: v for k, v in err.items() if k != "input"}
        for err in errors
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": safe_errors},
    )


# =================================================================
# ROUTERS
# =================================================================
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(generation_router)
app.include_router(deploy_router)
app.include_router(prospecting_router)
app.include_router(payments_router, prefix="/api/payments")


# =================================================================
# FRONTEND ESTATICO
# =================================================================
@app.get("/google022d0f40a84805e0.html")
async def google_verification():
    return FileResponse("../front/google022d0f40a84805e0.html")
    
@app.get("/chat")
async def get_chat_page():
    return FileResponse("../front/chat.html")

@app.get("/checkout")
async def get_checkout_page():
    return FileResponse("../front/checkout.html")

@app.get("/api/config")
async def get_public_config():
    """Retorna configurações públicas necessárias no frontend."""
    return {
        "mp_public_key": os.getenv("MP_PUBLIC_KEY", ""),
    }

if os.path.exists("../front"):
    if os.path.exists("../front/assets"):
        app.mount("/assets", StaticFiles(directory="../front/assets"), name="assets")
    if os.path.exists("../front/img"):
        app.mount("/img", StaticFiles(directory="../front/img"), name="img")
    app.mount("/", StaticFiles(directory="../front", html=True), name="front")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)