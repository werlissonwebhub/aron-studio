import json
import re
import aiosqlite
from fastapi import HTTPException
from config import DB_NAME

# INICIALIZAÇÃO DO BANCO
# =================================================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Tabela de Usuários
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT,
                name TEXT,
                credits INTEGER DEFAULT 0,
                has_received_welcome_bonus BOOLEAN DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # MIGRATIONS: Garantir que colunas adicionadas depois existam
        try:
            await db.execute("ALTER TABLE payment_attempts ADD COLUMN plan_id TEXT")
            await db.commit()
        except: pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
            await db.commit()
        except: pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN name TEXT")
            await db.commit()
            print(">>> [DB] Coluna 'name' migrada com sucesso.")
        except: pass

        try:
            await db.execute("ALTER TABLE users ADD COLUMN has_received_welcome_bonus BOOLEAN DEFAULT 0")
            await db.commit()
            print(">>> [DB] Coluna 'has_received_welcome_bonus' migrada com sucesso.")
        except: pass

        try:
            await db.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
            await db.commit()
            print(">>> [DB] Coluna 'updated_at' migrada com sucesso.")
        except: pass

        # Tabela de Chats/Projetos
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                full_code TEXT,
                mode TEXT,
                thumbnail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Tabelas de Pagamento (Necessárias para payments.py)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payment_attempts (
                payment_id TEXT PRIMARY KEY,
                user_id TEXT,
                user_email TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processed_payments (
                payment_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Tabela de Logs de Crédito
        await db.execute("""
            CREATE TABLE IF NOT EXISTS credit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                chat_id TEXT,
                amount INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        

        try:
            await db.execute("ALTER TABLE chats ADD COLUMN thumbnail TEXT")
            await db.commit()
            print(">>> [DB] Coluna 'thumbnail' migrada com sucesso.")
        except: pass

        # INDICES para performance com muitos usuarios
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chats_user_created ON chats(user_id, created_at DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_credit_logs_user ON credit_logs(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_payment_attempts_user ON payment_attempts(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_processed_payments ON processed_payments(payment_id)")
        await db.commit()
        print(">>> [DB] Indices criados com sucesso.")
        # Migração: Adicionar coluna 'has_received_welcome_bonus' se não existir
        try:
            await db.execute("ALTER TABLE users ADD COLUMN has_received_welcome_bonus BOOLEAN DEFAULT 0")
        except:
            pass # Coluna já existe
            
        # Migração: Adicionar coluna 'mode' se não existir
        try:
            await db.execute("ALTER TABLE chats ADD COLUMN mode TEXT")
        except:
            pass # Já existe
            
        # Migração: Adicionar coluna 'updated_at' se não existir na tabela chats
        try:
            await db.execute("ALTER TABLE chats ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except:
            pass # Já existe
            
        await db.commit()


# =================================================================
# UTILITÁRIOS E HELPERS
# =================================================================
async def validate_user(user_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(status_code=401, detail="Acesso negado: Usuário inexistente")

async def check_credit_availability(user_id: str, amount: int = 1) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT credits FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] >= amount:
                return True
    return False

async def consume_credit(user_id: str, chat_id: str, amount: int = 1) -> bool:
    """
    Consome créditos de forma ATÔMICA para evitar Race Conditions.
    Retorna True se o consumo foi realizado com sucesso.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # UPDATE Atômico: Só desconta se houver saldo
        cursor = await db.execute(
            "UPDATE users SET credits = credits - ? WHERE id = ? AND credits >= ?",
            (amount, user_id, amount)
        )
        if cursor.rowcount > 0:
            # Registrar Log de Transação
            await db.execute(
                "INSERT INTO credit_logs (user_id, chat_id, amount, reason) VALUES (?, ?, ?, ?)",
                (user_id, chat_id, amount, "generation_success")
            )
            await db.commit()
            
            # Buscar novo saldo para log
            async with db.execute("SELECT credits FROM users WHERE id = ?", (user_id,)) as res:
                row = await res.fetchone()
                novo_saldo = row[0] if row else '?'
                print(f">>> [CREDITS] Usuário {user_id} consumiu {amount} crédito. Novo saldo: {novo_saldo}")
                
            return True
        return False

# --- UTILS PARA LIMPEZA E REPARO DE JSON ---
def robust_json_cleaner(text: str) -> str:
    """
    Limpa e extrai o bloco JSON de uma resposta da IA, 
    tentando reparar truncamentos comuns.
    """
    if not text:
        return ""
        
    # 1. Limpeza de Markdown e caracteres de controle
    clean = text.replace("```json", "").replace("```html", "").replace("```", "").strip()
    
    # 2. Localização e Extração Cirúrgica via Regex (Garante que nada escape após o último })
    match = re.search(r'\{[\s\S]*\}', clean)
    if match:
        json_candidate = match.group(0)
    else:
        # Fallback se não achar chaves — talvez seja código puro
        return clean
        
    # 3. Tentativa de Reparo para Truncamento
    open_braces = json_candidate.count('{')
    close_braces = json_candidate.count('}')
    open_quotes = json_candidate.count('"')
    
    if open_quotes % 2 != 0:
        json_candidate += '"'
    if open_braces > close_braces:
        json_candidate += '}' * (open_braces - close_braces)
        
    # 4. Limpeza de caracteres de controle invisíveis
    json_candidate = "".join(ch for ch in json_candidate if ord(ch) >= 32 or ch in "\n\r\t")

    # 5. Validação Final
    try:
        json.loads(json_candidate)
        return json_candidate
    except:
        return json_candidate
