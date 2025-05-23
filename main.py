# main.py

import os
import logging

from fastapi import FastAPI, Form, HTTPException
from dotenv import load_dotenv
import openai

from utils import send_message

# 1) Carga las variables de entorno (.env)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 2) Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3) Inicializa FastAPI
app = FastAPI()

@app.post("/message")
async def whatsapp_webhook(
    From: str = Form(...),   # p.ej. "whatsapp:+50685005444"
    Body: str = Form(...)    # texto enviado por el usuario
):
    # 4) Extrae el número sin prefijo
    user_number = From.replace("whatsapp:", "")

    try:
        # 5) Genera la respuesta con la nueva API de Chat Completions
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[{"role": "user", "content": Body}],
            max_tokens=150,
            temperature=0.7
        )
        bot_text = resp.choices[0].message.content.strip()

        # 6) Envía la respuesta por WhatsApp
        send_message(user_number, bot_text)

    except Exception:
        # 7) Loguea toda la excepción y devuelve un 500
        logger.exception("Error en /message:")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

    # 8) Twilio no espera ningún cuerpo en el response
    return ""
