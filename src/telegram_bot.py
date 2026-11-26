import asyncio
import os

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
DONO_ID = os.getenv("TELEGRAM_USER_ID", "").strip()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


def autorizado(update: Update) -> bool:
    return bool(DONO_ID) and str(update.effective_user.id) == DONO_ID


async def meuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    await msg.reply_text(f"Seu ID é: {update.effective_user.id}")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    msg = update.effective_message
    try:
        async with httpx.AsyncClient(timeout=30) as http:
            await http.post(f"{API_URL}/reset")
        await msg.reply_text("Memória apagada.")
    except httpx.HTTPError:
        await msg.reply_text("Não consegui falar com o servidor do Me Ajuda.")


async def conversar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    msg = update.effective_message
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    try:
        async with httpx.AsyncClient(timeout=60) as http:
            r = await http.post(f"{API_URL}/chat", json={"texto": msg.text})
        if r.status_code == 200:
            await msg.reply_text(r.json()["resposta"])
        else:
            await msg.reply_text("O Me Ajuda está com dificuldade agora. Tente de novo em instantes.")
    except httpx.HTTPError:
        await msg.reply_text("Não consegui falar com o servidor do Me Ajuda. Ele está ligado?")


def main():
    if not TOKEN:
        raise SystemExit("Falta o TELEGRAM_TOKEN no arquivo .env")
    asyncio.set_event_loop(asyncio.new_event_loop())  # compatibilidade com Python novo
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("meuid", meuid))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, conversar))
    print("Bot do Me Ajuda ligado. Ctrl+C para parar.")
    app.run_polling()


if __name__ == "__main__":
    main()