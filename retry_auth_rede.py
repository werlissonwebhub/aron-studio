# CORRECAO: falha de rede transitoria estava barrando usuarios legitimos com 401.
# O Firebase Admin busca as chaves publicas do Google para validar o token.
# Se essa conexao falhar (SSL/timeout/DNS), o usuario era rejeitado na hora.
# Agora: 3 tentativas em falhas de REDE. Tokens realmente invalidos continuam
# sendo rejeitados imediatamente (sem retry, que seria inutil).
import shutil, os
if os.path.exists("server/security.py"):
    shutil.copy("server/security.py", "server/security.py.bak")
    print("backup: server/security.py.bak")
    print()

import ast, sys

path = "server/security.py"
with open(path, "r", encoding="utf-8", newline="") as f:
    c = f.read()

eol = "\r\n" if "\r\n" in c else "\n"

# Adicionar helper de retry logo apos a definicao de DEV_MODE
anchor = 'DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"'
if c.count(anchor) != 1:
    print("FALHOU: ancora DEV_MODE"); sys.exit(1)

helper = '''

# =================================================================
# VERIFICACAO COM RETRY
# O Firebase Admin precisa buscar as chaves publicas do Google para
# validar o token. Uma falha de rede transitoria (SSL, DNS, timeout)
# nao pode derrubar o login de um usuario legitimo — por isso tentamos
# novamente antes de rejeitar.
# =================================================================
import asyncio as _asyncio

_NETWORK_HINTS = (
    "ssl", "connection", "timeout", "timed out", "temporarily",
    "unreachable", "reset by peer", "handshake", "eof occurred",
    "max retries exceeded", "httpsconnectionpool", "name resolution",
)


def _is_network_error(err: Exception) -> bool:
    """True se o erro parece ser de rede (e nao um token realmente invalido)."""
    msg = str(err).lower()
    return any(h in msg for h in _NETWORK_HINTS)


async def _verify_with_retry(token: str, tentativas: int = 3):
    """
    Valida o ID token com retry em falhas de REDE.
    Tokens invalidos/expirados/revogados falham na hora (sem retry),
    porque tentar de novo nao mudaria o resultado.
    """
    from firebase_admin import auth as _auth

    ultimo = None
    for i in range(tentativas):
        try:
            return _auth.verify_id_token(token, check_revoked=True)
        except (_auth.ExpiredIdTokenError, _auth.RevokedIdTokenError,
                _auth.UserDisabledError, _auth.InvalidIdTokenError):
            raise  # erro real do token: nao adianta tentar de novo
        except Exception as e:
            ultimo = e
            if not _is_network_error(e) or i == tentativas - 1:
                raise
            espera = 0.6 * (i + 1)
            print(f">>> [AUTH] Falha de rede ao validar token "
                  f"(tentativa {i+1}/{tentativas}). Repetindo em {espera}s...")
            await _asyncio.sleep(espera)
    raise ultimo
'''

c = c.replace(anchor, anchor + helper.replace("\n", eol), 1)

# Trocar as chamadas diretas por _verify_with_retry nas duas funcoes
old_call = "        decoded = auth.verify_id_token(token, check_revoked=True)" + eol + "        uid = decoded[\"uid\"]"
new_call = "        decoded = await _verify_with_retry(token)" + eol + "        uid = decoded[\"uid\"]"
if c.count(old_call) == 1:
    c = c.replace(old_call, new_call, 1)
    print("  + verify_firebase_token: retry ativado")
else:
    print("  ! verify_firebase_token: nao encontrei a chamada"); sys.exit(1)

old_call2 = "        decoded = auth.verify_id_token(token, check_revoked=True)" + eol + "        return {"
new_call2 = "        decoded = await _verify_with_retry(token)" + eol + "        return {"
if c.count(old_call2) == 1:
    c = c.replace(old_call2, new_call2, 1)
    print("  + verify_firebase_token_full: retry ativado")
else:
    print("  ! verify_firebase_token_full: nao encontrei"); sys.exit(1)

try:
    ast.parse(c)
except SyntaxError as e:
    print("ERRO SINTAXE:", e); sys.exit(1)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(c)
print()
print("OK - falhas de rede agora tem 3 tentativas antes de barrar o usuario")
print("Sintaxe Python: valida")
