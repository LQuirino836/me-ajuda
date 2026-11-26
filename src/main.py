import os
import time
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


def criar_chat():
    return client.chats.create(
        model=MODELO,
        config=types.GenerateContentConfig(system_instruction=INSTRUCAO),
    )


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
    return {"status": "Me Ajuda está online"}


@app.post("/chat")
def chat(mensagem: Mensagem):
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
    return {"resposta": resposta.text}


@app.post("/reset")
def reset():
    global chat_sessao
    chat_sessao = criar_chat()
    return {"status": "memória apagada"}