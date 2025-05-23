# main.py

import os
import logging
from settings import settings

from fastapi import FastAPI, Form, HTTPException, Request, Header
from dotenv import load_dotenv
import openai
from twilio.request_validator import RequestValidator

from utils import send_message
from models import SessionLocal, Conversation

# 1) Carga variables de entorno
load_dotenv()
openai.api_key = settings.openai_api_key
twilio_auth_token = settings.twilio_auth_token

# 2) Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3) Inicializa FastAPI
app = FastAPI()

@app.post("/message")
async def whatsapp_webhook(
    request: Request,
    X_Twilio_Signature: str = Header(...),  # Cabecera con la firma de Twilio
    From: str = Form(...),                  # "whatsapp:+506..."
    Body: str = Form(...)                   # Texto del mensaje
):
    # 4) Validar firma
    validator = RequestValidator(twilio_auth_token)
    url = str(request.url)
    form = await request.form()
    # Twilio envía el cuerpo como dict de str->str
    if not validator.validate(url, dict(form), X_Twilio_Signature):
        logger.warning("Firma Twilio no válida")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    user_number = From.replace("whatsapp:", "")

    try:
        # 5) Generar respuesta con OpenAI (Chat Completions)
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": Body}],
            max_tokens=150,
            temperature=0.7
        )
        bot_text = resp.choices[0].message.content.strip()

        # 6) Enviar respuesta por WhatsApp
        send_message(user_number, bot_text)

        # 7) Persistir en la BD
        db = SessionLocal()
        convo = Conversation(sender=user_number, message=Body, response=bot_text)
        db.add(convo)
        db.commit()
        db.close()

    except Exception:
        logger.exception("Error en /message:")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

    # 8) Respuesta vacía a Twilio
    return ""
