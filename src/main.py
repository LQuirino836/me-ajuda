import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types, errors

load_dotenv()

app = FastAPI(title="Me Ajuda")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODELO = os.getenv("GEMINI_MODEL")

INSTRUCAO = """Você é o Me Ajuda, um assistente pessoal.
Responda sempre em português do Brasil, de forma clara e curta.
Seja gentil e direto."""

TENTATIVAS = 3
ESPERA_INICIAL = 2
ERROS_TEMPORARIOS = (429, 500, 503, 504)

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_MEMORIA = PASTA_PROJETO / "dados" / "memoria.json"
MAX_MENSAGENS = 40


def carregar_memoria():
    if not ARQUIVO_MEMORIA.exists():
        return []
    try:
        return json.loads(ARQUIVO_MEMORIA.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def salvar_memoria():
    ARQUIVO_MEMORIA.parent.mkdir(exist_ok=True)
    texto = json.dumps(historico, ensure_ascii=False, indent=2)
    ARQUIVO_MEMORIA.write_text(texto, encoding="utf-8")


def criar_chat():
    contents = [
        types.Content(role=m["papel"], parts=[types.Part(text=m["texto"])])
        for m in historico
    ]
    return client.chats.create(
        model=MODELO,
        config=types.GenerateContentConfig(system_instruction=INSTRUCAO),
        history=contents,
    )


historico = carregar_memoria()
chat_sessao = criar_chat()


def enviar_com_retry(texto):
    espera = ESPERA_INICIAL
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return chat_sessao.send_message(texto)
        except errors.APIError as erro:
            temporario = erro.code in ERROS_TEMPORARIOS
            if not temporario or tentativa == TENTATIVAS:
                raise
            time.sleep(espera)
            espera *= 2


class Mensagem(BaseModel):
    texto: str


@app.get("/")
def status():
    return {"status": "Me Ajuda está online", "mensagens_na_memoria": len(historico)}


@app.post("/chat")
def chat(mensagem: Mensagem):
    global chat_sessao
    try:
        resposta = enviar_com_retry(mensagem.texto)
    except errors.APIError as erro:
        if erro.code in ERROS_TEMPORARIOS:
            raise HTTPException(
                status_code=503,
                detail="O Gemini está ocupado agora. Tente de novo em instantes.",
            )
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao falar com o Gemini (código {erro.code}).",
        )

    if not resposta.text:
        chat_sessao = criar_chat()
        raise HTTPException(
            status_code=502,
            detail="O Gemini não devolveu texto. Tente reformular.",
        )

    historico.append({"papel": "user", "texto": mensagem.texto})
    historico.append({"papel": "model", "texto": resposta.text})

    if len(historico) > MAX_MENSAGENS:
        del historico[:-MAX_MENSAGENS]
        chat_sessao = criar_chat()

    salvar_memoria()
    return {"resposta": resposta.text}


@app.post("/reset")
def reset():
    global chat_sessao
    historico.clear()
    salvar_memoria()
    chat_sessao = criar_chat()
    return {"status": "memória apagada"}