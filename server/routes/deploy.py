import os
import re
import hashlib
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from database import validate_user
from security import verify_firebase_token, DEV_MODE, limiter

router = APIRouter()


def sanitize_name(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:50] or "aron-project"


def user_slug(user_id: str) -> str:
    """Hash curto e estavel do user_id, usado para namespacar o projeto no
    Vercel por usuario — evita que dois clientes com o mesmo nome de projeto
    colidam e sobrescrevam o deploy um do outro."""
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:8]


@router.post("/deploy")
@limiter.limit("5/minute")
async def deploy_project(request: Request, verified_uid: str = Depends(verify_firebase_token)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body JSON invalido")

    user_id   = data.get("user_id")
    html_code = data.get("html_code") or data.get("full_code") or data.get("code")
    name      = data.get("name") or data.get("title") or "Aron Project"

    if not html_code:
        raise HTTPException(status_code=400, detail="html_code e obrigatorio")

    if not DEV_MODE and verified_uid != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    if user_id:
        await validate_user(user_id)

    vercel_token = os.getenv("VERCEL_TOKEN")
    if not vercel_token:
        raise HTTPException(status_code=500, detail="VERCEL_TOKEN nao configurado")

    project_name = f"aron-{sanitize_name(name)}"
    if user_id:
        project_name = f"aron-{user_slug(user_id)}-{sanitize_name(name)}"

    payload = {
        "name": project_name,
        "files": [
            {
                "file": "index.html",
                "data": html_code,
                "encoding": "utf-8"
            }
        ],
        "projectSettings": {
            "framework": None,
            "buildCommand": None,
            "outputDirectory": None,
            "installCommand": None
        },
        "target": "production"
    }

    headers = {
        "Authorization": f"Bearer {vercel_token}",
        "Content-Type": "application/json"
    }

    print(f">>> [DEPLOY] Iniciando: {project_name} | user: {user_id}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.vercel.com/v13/deployments",
                headers=headers,
                json=payload
            )

        result = response.json()
        print(f">>> [DEPLOY] Status: {response.status_code} | url: {result.get('url', 'sem url')}")

        if response.status_code in [200, 201]:
            deploy_url = result.get("url", "")
            if deploy_url and not deploy_url.startswith("http"):
                deploy_url = f"https://{deploy_url}"
            return {
                "status": "success",
                "url": deploy_url,
                "name": project_name,
                "deployment_id": result.get("id", "")
            }

        error_msg = result.get("error", {}).get("message", str(result))
        print(f">>> [DEPLOY ERROR] {response.status_code}: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Vercel erro {response.status_code}: {error_msg}"
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout na Vercel")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no deploy: {str(e)}")
