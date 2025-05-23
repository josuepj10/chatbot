# main.py

import logging
from fastapi import FastAPI, Form, HTTPException, Request, Header, BackgroundTasks
from dotenv import load_dotenv
import openai
from twilio.request_validator import RequestValidator

from utils import send_message
from models import SessionLocal, Conversation
from settings import settings

# 1) Carga variables de entorno
load_dotenv()
openai.api_key = settings.openai_api_key
twilio_auth_token = settings.twilio_auth_token

# 2) Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3) Inicializa FastAPI
app = FastAPI()

def handle_response(user_number: str, body: str, bot_text: str):
    """
    Función que se ejecuta en background para:
     - enviar el mensaje por WhatsApp
     - guardar la conversación en la BD
    """
    try:
        # Envía el WhatsApp
        send_message(user_number, bot_text)
        # Persiste en la BD
        db = SessionLocal()
        convo = Conversation(sender=user_number, message=body, response=bot_text)
        db.add(convo)
        db.commit()
    except Exception:
        logger.exception("Error en background task")
    finally:
        db.close()

@app.post("/message")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    request: Request,
    X_Twilio_Signature: str = Header(...),
    From: str            = Form(...),
    Body: str            = Form(...)
):
    # 4) Validar firma de Twilio
    validator = RequestValidator(twilio_auth_token)
    url       = str(request.url)
    form      = await request.form()
    if not validator.validate(url, dict(form), X_Twilio_Signature):
        logger.warning("Firma Twilio no válida")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    user_number = From.replace("whatsapp:", "")

    # 5) Llamada a OpenAI (sin bloquear el webhook)
    try:
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": Body}],
            max_tokens=150,
            temperature=0.7
        )
        bot_text = resp.choices[0].message.content.strip()
    except Exception:
        logger.exception("Error generando respuesta con OpenAI")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

    # 6) Programa el envío y guardado en background
    background_tasks.add_task(handle_response, user_number, Body, bot_text)

    # 7) Twilio solo necesita un 200 OK
    return ""
