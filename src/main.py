import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai

load_dotenv()

app = FastAPI(title="Me Ajuda")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODELO = os.getenv("GEMINI_MODEL")


class Mensagem(BaseModel):
    texto: str


@app.get("/")
def status():
    return {"status": "Me Ajuda está online"}


@app.post("/chat")
def chat(mensagem: Mensagem):
    resposta = client.models.generate_content(
        model=MODELO,
        contents=mensagem.texto,
    )
    return {"resposta": resposta.text}