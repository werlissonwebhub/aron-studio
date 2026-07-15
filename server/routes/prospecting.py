"""
routes/prospecting.py — Sistema de Prospecção de Empresas Sem Site

Fontes de dados combinadas:
  1. Google Places API  — busca principal (requer chave)
  2. Overpass API       — OpenStreetMap, gratuita sem chave
  3. BrasilAPI          — cidades brasileiras por estado

Endpoints:
  POST /api/prospecting/search       — busca leads sem site
  POST /api/prospecting/save         — salva um lead
  GET  /api/prospecting/leads        — lista leads salvos
  GET  /api/prospecting/cities/{uf}  — cidades de um estado (BrasilAPI)
"""

import os
import asyncio
import aiosqlite
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import DB_NAME, validate_user
from security import verify_firebase_token, DEV_MODE

router = APIRouter()

PLACES_KEY     = os.getenv("GOOGLE_PLACES_API_KEY", "")
PLACES_SEARCH  = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"
OVERPASS_URL   = "https://overpass-api.de/api/interpreter"
BRASILAPI_URL  = "https://brasilapi.com.br/api/ibge/municipios/v1"

# Redes sociais nao contam como site profissional
SOCIAL_MEDIA = [
    'facebook.com', 'fb.com', 'instagram.com', 'linktr.ee',
    'wa.me', 'whatsapp.com', 'twitter.com', 'x.com',
    'youtube.com', 'tiktok.com', 'snapchat.com', 'linkedin.com'
]

# Mapeamento categoria → tags OpenStreetMap
OSM_TAGS = {
    'restaurante':     [('amenity', 'restaurant'), ('amenity', 'fast_food')],
    'restaurantes':    [('amenity', 'restaurant'), ('amenity', 'fast_food')],
    'clinica':         [('amenity', 'clinic'), ('healthcare', 'clinic')],
    'clinicas':        [('amenity', 'clinic'), ('healthcare', 'clinic')],
    'salao':           [('shop', 'hairdresser'), ('shop', 'beauty')],
    'saloes':          [('shop', 'hairdresser'), ('shop', 'beauty')],
    'academia':        [('leisure', 'fitness_centre'), ('sport', 'fitness')],
    'academias':       [('leisure', 'fitness_centre')],
    'advogado':        [('office', 'lawyer')],
    'advogados':       [('office', 'lawyer')],
    'farmacia':        [('amenity', 'pharmacy')],
    'farmacias':       [('amenity', 'pharmacy')],
    'oficina':         [('shop', 'car_repair')],
    'oficinas':        [('shop', 'car_repair')],
    'loja':            [('shop', 'clothes'), ('shop', 'general')],
    'lojas':           [('shop', 'clothes'), ('shop', 'general')],
    'padaria':         [('shop', 'bakery')],
    'padarias':        [('shop', 'bakery')],
    'supermercado':    [('shop', 'supermarket')],
    'supermercados':   [('shop', 'supermarket')],
    'hotel':           [('tourism', 'hotel'), ('tourism', 'guest_house')],
    'hoteis':          [('tourism', 'hotel')],
    'escola':          [('amenity', 'school')],
    'escolas':         [('amenity', 'school')],
    'contabilidade':   [('office', 'accountant')],
    'dentista':        [('amenity', 'dentist'), ('healthcare', 'dentist')],
    'dentistas':       [('amenity', 'dentist')],
    'mecanica':        [('shop', 'car_repair')],
    'pet shop':        [('shop', 'pet')],
    'veterinario':     [('amenity', 'veterinary')],
    'pizzaria':        [('amenity', 'restaurant'), ('cuisine', 'pizza')],
    'bar':             [('amenity', 'bar'), ('amenity', 'pub')],
    'bares':           [('amenity', 'bar')],
    'autoescola':      [('amenity', 'driving_school')],
}


# =================================================================
# MODELOS
# =================================================================
class ProspectingRequest(BaseModel):
    query:       str
    user_id:     str
    max_results: int = 20
    source:      str = "all"   # "google" | "osm" | "all"


class SaveLeadRequest(BaseModel):
    user_id:       str
    place_id:      str
    business_name: str
    category:      str
    city:          str
    address:       str
    phone:         Optional[str] = ""
    website:       Optional[str] = ""
    rating:        Optional[float] = 0.0


# =================================================================
# HELPERS
# =================================================================
def has_real_website(url: str) -> bool:
    """Retorna False se URL for rede social ou vazia."""
    if not url:
        return False
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower().replace('www.', '')
        return not any(s in domain for s in SOCIAL_MEDIA)
    except Exception:
        return False


async def website_is_live(url: str) -> bool:
    """Verifica se um site está no ar."""
    if not url:
        return False
    try:
        if not url.startswith("http"):
            url = "https://" + url
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, verify=False) as c:
            resp = await c.head(url)
            return resp.status_code < 400
    except Exception:
        return False


async def get_place_details(place_id: str, client: httpx.AsyncClient) -> dict:
    """Busca website e telefone de um lugar via Place Details API."""
    try:
        resp = await client.get(
            PLACES_DETAILS,
            params={
                "place_id": place_id,
                "fields":   "website,formatted_phone_number",
                "key":      PLACES_KEY,
                "language": "pt-BR",
            },
            timeout=8.0,
        )
        if resp.status_code == 200:
            return resp.json().get("result", {})
    except Exception as e:
        print(f">>> [PROSPECTING] Details error: {e}")
    return {}


async def ensure_leads_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS prospecting_leads (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       TEXT,
                place_id      TEXT,
                business_name TEXT,
                category      TEXT,
                city          TEXT,
                address       TEXT,
                phone         TEXT,
                website       TEXT,
                rating        REAL DEFAULT 0,
                status        TEXT DEFAULT 'novo',
                source        TEXT DEFAULT 'google',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            await db.execute("ALTER TABLE prospecting_leads ADD COLUMN source TEXT DEFAULT 'google'")
        except Exception:
            pass
        await db.commit()


# =================================================================
# BUSCA VIA GOOGLE PLACES API
# =================================================================
async def search_google(query: str, max_results: int) -> List[dict]:
    if not PLACES_KEY:
        print(">>> [PROSPECTING] Google Places key não configurada — pulando")
        return []

    leads = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                PLACES_SEARCH,
                params={"query": query, "key": PLACES_KEY, "language": "pt-BR", "region": "br"}
            )

        data = resp.json()
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            print(f">>> [GOOGLE] Status: {data.get('status')} — {data.get('error_message','')}")
            return []

        places = data.get("results", [])
        print(f">>> [GOOGLE] {len(places)} lugares encontrados")

        async with httpx.AsyncClient(timeout=10.0) as client:
            details = await asyncio.gather(
                *[get_place_details(p["place_id"], client) for p in places[:25]],
                return_exceptions=True
            )

        for place, det in zip(places[:25], details):
            if isinstance(det, Exception):
                det = {}

            website = det.get("website", "")
            phone   = det.get("formatted_phone_number", "")
            is_real = has_real_website(website)

            # Verificar se site está no ar (com timeout curto de 3s)
            live = False
            if is_real and website:
                try:
                    live = await asyncio.wait_for(website_is_live(website), timeout=3.0)
                except Exception:
                    live = False  # timeout = site inacessível = lead

            # Incluir como lead se:
            # 1. Não tem site nenhum
            # 2. Tem só rede social (Facebook, Instagram etc)
            # 3. Tem site mas está fora do ar/inacessível
            if not live:
                badge = "Sem site" if not website else ("Só redes sociais" if not is_real else "Site offline")
                leads.append({
                    "place_id":  place.get("place_id", ""),
                    "name":      place.get("name", ""),
                    "address":   place.get("formatted_address", ""),
                    "phone":     phone,
                    "website":   website,
                    "rating":    place.get("rating", 0),
                    "is_social": bool(website) and not is_real,
                    "badge":     badge,
                    "source":    "Google Maps",
                })
                print(f">>> [LEAD] '{place.get('name')}' — {badge}")

            if len(leads) >= max_results:
                break

    except Exception as e:
        print(f">>> [GOOGLE ERROR] {e}")

    return leads


# =================================================================
# BUSCA VIA OVERPASS API (OpenStreetMap) — SEM CHAVE
# =================================================================

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

async def query_overpass(query: str) -> list:
    """Tenta múltiplos servidores Overpass até um responder."""
    for server in OVERPASS_SERVERS:
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    server,
                    data={"data": query},
                    headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
                )
            if resp.status_code == 200:
                raw = resp.text.strip()
                if raw and raw.startswith("{"):
                    elements = resp.json().get("elements", [])
                    print(f">>> [OSM] Servidor OK: {len(elements)} elementos")
                    return elements
        except Exception as e:
            print(f">>> [OSM] Servidor falhou: {e}")
    return []


async def search_overpass(category: str, city: str, state: str, max_results: int) -> list:
    """Busca negócios no OpenStreetMap — gratuito e sem chave de API."""
    city_normalized = city.title().strip()
    cat_lower = category.lower().strip()
    tags = OSM_TAGS.get(cat_lower, [])
    if not tags:
        for key, val in OSM_TAGS.items():
            if key in cat_lower or cat_lower in key:
                tags = val
                break
    if not tags:
        tags = [("amenity", "restaurant")]

    leads = []
    try:
        print(f">>> [OSM] Buscando: {category} em {city_normalized}, {state}")
        async with httpx.AsyncClient(timeout=12.0) as client:
            loc_resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{city_normalized}, {state}, Brasil", "format": "json", "limit": 1, "countrycodes": "br"},
                headers={"User-Agent": "AronStudio/1.0 (aronstudio.com.br)"}
            )

        if loc_resp.status_code != 200:
            return []
        raw_loc = loc_resp.text.strip()
        if not raw_loc or not raw_loc.startswith("["):
            return []
        locs = loc_resp.json()
        if not locs:
            print(f">>> [OSM] Cidade nao encontrada: {city_normalized}")
            return []

        bbox = locs[0].get("boundingbox", [])
        print(f">>> [OSM] Cidade encontrada: {locs[0].get('display_name','')[:60]}")
        if len(bbox) < 4:
            return []

        s, n, w, e = bbox[0], bbox[1], bbox[2], bbox[3]
        bb = f"{s},{w},{n},{e}"

        tag_filters = ""
        for k, v in tags:
            tag_filters += f'  node["{k}"="{v}"]({bb});\n'
            tag_filters += f'  way["{k}"="{v}"]({bb});\n'

        overpass_query = f"""[out:json][timeout:20];
(
{tag_filters}
);
out body;"""

        elements = await query_overpass(overpass_query)
        print(f">>> [OSM] {len(elements)} elementos encontrados")

        for el in elements:
            el_tags = el.get("tags", {})
            name = el_tags.get("name", "").strip()
            if not name:
                continue
            website = (el_tags.get("website") or el_tags.get("contact:website") or "").strip()
            phone   = (el_tags.get("phone") or el_tags.get("contact:phone") or el_tags.get("contact:mobile") or "").strip()
            street  = el_tags.get("addr:street", "")
            number  = el_tags.get("addr:housenumber", "")
            address = f"{street}, {number}".strip(", ") if street else f"{city_normalized}, {state}"

            is_real = has_real_website(website)
            live = False
            if is_real and website:
                try:
                    live = await asyncio.wait_for(website_is_live(website), timeout=3.0)
                except Exception:
                    live = False

            if not live:
                badge = "Sem site" if not website else ("So redes sociais" if not is_real else "Site offline")
                leads.append({
                    "place_id": f"osm_{el.get('id', '')}",
                    "name":     name,
                    "address":  address,
                    "phone":    phone,
                    "website":  website,
                    "rating":   0,
                    "is_social": bool(website) and not is_real,
                    "badge":    badge,
                    "source":   "OpenStreetMap",
                })
                print(f">>> [OSM LEAD] '{name}' — {badge}")
            if len(leads) >= max_results:
                break

    except Exception as e:
        import traceback
        print(f">>> [OSM ERROR] {e}\n{traceback.format_exc()}")

    return leads
# =================================================================
# ENDPOINT PRINCIPAL DE BUSCA
# =================================================================
@router.post("/api/prospecting/search")
async def search_businesses(req: ProspectingRequest, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != req.user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    await validate_user(req.user_id)
    await ensure_leads_table()

    # Extrair cidade e estado da query
    # Formato esperado: "restaurantes em Fortaleza CE Brasil"
    query_lower = req.query.lower()
    parts = req.query.split(" em ", 1)
    category = parts[0].strip() if len(parts) > 1 else req.query
    location = parts[1].strip() if len(parts) > 1 else ""

    # Separar cidade e estado
    loc_parts = location.replace(" Brasil", "").replace(", Brasil", "").split(",")
    city  = loc_parts[0].strip() if loc_parts else location
    state = loc_parts[1].strip() if len(loc_parts) > 1 else ""

    print(f">>> [PROSPECTING] Categoria: '{category}' | Cidade: '{city}' | Estado: '{state}'")

    all_leads = []

    # Busca paralela: Google + OSM
    tasks = []
    if req.source in ("all", "google"):
        tasks.append(search_google(req.query, req.max_results))
    if req.source in ("all", "osm"):
        tasks.append(search_overpass(category, city, state, req.max_results))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Combinar resultados evitando duplicatas por nome
    seen_names = set()
    for result in results:
        if isinstance(result, list):
            for lead in result:
                name_key = lead["name"].lower().strip()
                if name_key not in seen_names:
                    seen_names.add(name_key)
                    all_leads.append(lead)

    # Ordenar: sem site nenhum > rede social > site offline
    all_leads.sort(key=lambda x: (
        1 if x.get("website") else 0,
        x.get("rating", 0) * -1
    ))

    total = len(all_leads)
    leads = all_leads[:req.max_results]

    print(f">>> [PROSPECTING] Total de leads: {total} | Retornando: {len(leads)}")

    return {
        "leads":              leads,
        "total_found":        total,
        "leads_without_site": len([l for l in leads if not l.get("website")]),
        "query":              req.query,
        "sources":            list(set(l.get("source", "") for l in leads)),
    }


# =================================================================
# ENDPOINT DE CIDADES POR ESTADO (BrasilAPI)
# =================================================================
@router.get("/api/prospecting/cities/{uf}")
async def get_cities(uf: str):
    """Retorna todas as cidades de um estado via BrasilAPI."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{BRASILAPI_URL}/{uf.upper()}")

        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Estado não encontrado")

        cities = resp.json()
        return [{"name": c["nome"], "code": c.get("codigo_ibge", "")} for c in cities]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =================================================================
# SALVAR LEAD
# =================================================================
@router.post("/api/prospecting/save")
async def save_lead(req: SaveLeadRequest, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != req.user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    await validate_user(req.user_id)
    await ensure_leads_table()

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id FROM prospecting_leads WHERE user_id=? AND place_id=?",
            (req.user_id, req.place_id)
        ) as cur:
            if await cur.fetchone():
                return {"status": "already_saved"}

        await db.execute(
            """INSERT INTO prospecting_leads
               (user_id, place_id, business_name, category, city, address, phone, website, rating)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (req.user_id, req.place_id, req.business_name,
             req.category, req.city, req.address,
             req.phone or "", req.website or "", req.rating or 0)
        )
        await db.commit()

    return {"status": "saved"}


# =================================================================
# LISTAR LEADS SALVOS
# =================================================================
@router.get("/api/prospecting/leads")
async def get_leads(user_id: str, verified_uid: str = Depends(verify_firebase_token)):
    if not DEV_MODE and verified_uid != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    await validate_user(user_id)
    await ensure_leads_table()

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """SELECT id, business_name, category, city, address, phone,
                      website, rating, status, created_at
               FROM prospecting_leads WHERE user_id=?
               ORDER BY created_at DESC""",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()

    return [
        {"id": r[0], "name": r[1], "category": r[2], "city": r[3],
         "address": r[4], "phone": r[5], "website": r[6],
         "rating": r[7], "status": r[8], "created_at": r[9]}
        for r in rows
    ]