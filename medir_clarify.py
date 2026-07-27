# Script que o usuario roda: mede o clarify com e sem thinking
import sys, os, time
sys.stderr = sys.stdout
from dotenv import load_dotenv
load_dotenv(os.path.join("server", ".env"))
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"),
                      http_options=types.HttpOptions(api_version="v1alpha"))

INSTR = ("Voce e o Aron Interviewer. Analise o pedido e decida se tem detalhes suficientes. "
         "Pedidos vagos = ready false com ate 4 perguntas. Completos = ready true. "
         'Responda APENAS JSON: {"ready": false, "questions": [{"id":"x","pergunta":"...","tipo":"botoes","opcoes":["a","b"]}]}')

PEDIDO = "crie uma landing page para uma cafeteria"

def medir(nome, config):
    t0 = time.time()
    try:
        r = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=f"{INSTR}\n\nPEDIDO: {PEDIDO}",
            config=config
        )
        dt = time.time() - t0
        txt = (r.text or "")[:45].replace("\n", " ")
        print(f"  {nome:35} -> {dt:5.1f}s | {txt}", flush=True)
        return dt
    except Exception as e:
        dt = time.time() - t0
        print(f"  {nome:35} -> {dt:5.1f}s | ERRO: {str(e)[:45]}", flush=True)
        return dt

print("Aquecendo a conexao...", flush=True)
try:
    client.models.generate_content(model="gemini-3.5-flash", contents="oi",
                                   config=types.GenerateContentConfig(max_output_tokens=5))
except Exception:
    pass
print()

print("COMPARANDO:", flush=True)
print()

# 1. Como esta hoje
medir("HOJE (2048 tokens, com thinking)",
      types.GenerateContentConfig(max_output_tokens=2048))

# 2. Sem thinking
try:
    medir("SEM THINKING (budget=0)",
          types.GenerateContentConfig(
              max_output_tokens=2048,
              thinking_config=types.ThinkingConfig(thinking_budget=0)))
except Exception as e:
    print("  (thinking_config nao suportado nesta versao do SDK)", flush=True)

# 3. Sem thinking + menos tokens
try:
    medir("SEM THINKING + 700 tokens",
          types.GenerateContentConfig(
              max_output_tokens=700,
              temperature=0.2,
              thinking_config=types.ThinkingConfig(thinking_budget=0)))
except Exception:
    medir("SO 700 tokens", types.GenerateContentConfig(max_output_tokens=700, temperature=0.2))
