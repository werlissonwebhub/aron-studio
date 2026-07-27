# Reduz drasticamente os pontos de falha na autenticacao.
#
# ANTES: check_revoked=True -> o servidor consultava o Google a CADA
#        requisicao para saber se a sessao foi revogada. Isso deixava
#        tudo mais lento e transformava qualquer soluco de rede em 401.
#
# AGORA: valida o token localmente com as chaves publicas em cache
#        (padrao usado pela maioria dos produtos). Configuravel via
#        CHECK_REVOKED=true no .env se voce precisar da checagem estrita.
import shutil, os
if os.path.exists("server/security.py"):
    shutil.copy("server/security.py", "server/security.py.bak2")
    print("backup: server/security.py.bak2")
    print()

import ast, sys

path = "server/security.py"
with open(path, "r", encoding="utf-8", newline="") as f:
    c = f.read()

eol = "\r\n" if "\r\n" in c else "\n"

if "CHECK_REVOKED" in c:
    print("Ja aplicado"); sys.exit(0)

# 1. Adicionar a flag configuravel logo apos DEV_MODE
anchor = 'DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"'
if c.count(anchor) != 1:
    print("FALHOU: ancora DEV_MODE"); sys.exit(1)

flag = '''

# =================================================================
# CHECK_REVOKED
# True  -> consulta o Google a CADA requisicao (mais seguro, porem mais
#          lento e com muito mais chance de falhar por rede).
# False -> valida o token localmente com as chaves publicas em cache
#          (padrao da industria). Uma sessao revogada continua valida
#          ate o token expirar sozinho, em no maximo 1 hora.
#
# Recomendado: False. Ative apenas se precisar revogar sessoes na hora.
# =================================================================
CHECK_REVOKED = os.getenv("CHECK_REVOKED", "false").lower() == "true"
'''

c = c.replace(anchor, anchor + flag.replace("\n", eol), 1)

# 2. Usar a flag na verificacao
old = "            return _auth.verify_id_token(token, check_revoked=True)"
new = "            return _auth.verify_id_token(token, check_revoked=CHECK_REVOKED)"
if c.count(old) != 1:
    print("FALHOU: chamada verify_id_token nao encontrada"); sys.exit(1)
c = c.replace(old, new, 1)

try:
    ast.parse(c)
except SyntaxError as e:
    print("ERRO SINTAXE:", e); sys.exit(1)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(c)

print("OK - check_revoked agora e configuravel (padrao: false)")
print()
print("Efeito:")
print("  - Token validado LOCALMENTE (sem ida ao Google a cada request)")
print("  - Login e geracao ficam mais rapidos")
print("  - Muito menos chance de 401 por falha de rede")
print()
print("Para reativar a checagem estrita, adicione no .env:")
print("  CHECK_REVOKED=true")
