import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

resposta = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL"),
    contents="Apresente-se em uma frase como Me Ajuda, um assistente pessoal.",
)

print(resposta.text)