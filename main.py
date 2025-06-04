# main.py

import uuid
import logging

from fastapi import FastAPI, Form, HTTPException, Request, Header, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import openai
from twilio.request_validator import RequestValidator

from utils import send_message
from models import SessionLocal, Conversation, Client, ClientResource
from settings import settings

# 1) Carga variables de entorno
load_dotenv()
openai.api_key    = settings.openai_api_key
twilio_auth_token = settings.twilio_auth_token

# 2) Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3) Inicializa FastAPI
app = FastAPI()


# ------------------------------------------------------
# Dependencia para obtener la sesión de BD
# ------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------
# Dependencia para autenticar al cliente (API Key)
# ------------------------------------------------------
def get_current_client(
    x_client_api_key: str = Header(..., convert_underscores=False),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.api_key == x_client_api_key).first()
    if not client:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return client


# ------------------------------------------------------
# Esquemas Pydantic para validar requests
# ------------------------------------------------------
class ClientCreate(BaseModel):
    name: str

class ResourceCreate(BaseModel):
    name: str
    type: str
    content: str


# ------------------------------------------------------
# Endpoint para registrar un nuevo cliente
# ------------------------------------------------------
@app.post("/register", response_model=dict)
def register_client(
    info: ClientCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Client).filter(Client.name == info.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cliente ya registrado")

    new_api_key = str(uuid.uuid4())
    client = Client(name=info.name, api_key=new_api_key)
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"id": client.id, "name": client.name, "api_key": client.api_key}


# ------------------------------------------------------
# Endpoint para subir recursos del cliente
# ------------------------------------------------------
@app.post("/upload_resource", response_model=dict)
def upload_resource(
    resource: ResourceCreate,
    client: Client = Depends(get_current_client),
    db: Session   = Depends(get_db)
):
    """
    Permite al cliente subir un recurso (texto o JSON) que luego usará el bot.
    """
    new_res = ClientResource(
        client_id=client.id,
        name=resource.name,
        type=resource.type,
        content=resource.content
    )
    db.add(new_res)
    db.commit()
    db.refresh(new_res)
    return {
        "resource_id": new_res.id,
        "name":        new_res.name,
        "type":        new_res.type
    }


# ------------------------------------------------------
# Tu función de background y endpoint /message quedan igual
# ------------------------------------------------------
def handle_response(user_number: str, body: str, bot_text: str):
    try:
        send_message(user_number, bot_text)
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
    validator = RequestValidator(twilio_auth_token)
    url       = str(request.url)
    form      = await request.form()
    if not validator.validate(url, dict(form), X_Twilio_Signature):
        logger.warning("Firma Twilio no válida")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    user_number = From.replace("whatsapp:", "")

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

    background_tasks.add_task(handle_response, user_number, Body, bot_text)
    return ""
