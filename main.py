# main.py

import os
import logging

from fastapi import FastAPI, Form, HTTPException
from dotenv import load_dotenv
import openai

from utils import send_message
from models import SessionLocal, Conversation  # <— importamos tu sesión y modelo

# 1) Carga .env y configura OpenAI
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 2) Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3) Inicializa FastAPI
app = FastAPI()

@app.post("/message")
async def whatsapp_webhook(
    From: str = Form(...),   # p.ej. "whatsapp:+50685005444"
    Body: str = Form(...)    # el texto que envía el usuario
):
    # 4) Extraemos el número sin el prefijo "whatsapp:"
    user_number = From.replace("whatsapp:", "")

    try:
        # 5) Generamos la respuesta con la nueva API de Chat Completions
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": Body}],
            max_tokens=150,
            temperature=0.7
        )
        bot_text = resp.choices[0].message.content.strip()

        # 6) Enviamos la respuesta por WhatsApp
        send_message(user_number, bot_text)

        # 7) Persistimos la conversación en la BD
        db = SessionLocal()
        convo = Conversation(
            sender=user_number,
            message=Body,
            response=bot_text
        )
        db.add(convo)
        db.commit()
        db.close()

    except Exception:
        logger.exception("Error en /message:")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

    # 8) Twilio no necesita body de respuesta
    return ""
