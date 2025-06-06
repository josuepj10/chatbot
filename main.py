# main.py

import uuid
import json
import logging

from fastapi import FastAPI, Form, HTTPException, Request, Header, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import openai
from twilio.request_validator import RequestValidator

from utils import send_message
from models import (
    SessionLocal,
    Conversation,
    Client,
    ClientResource
)
from settings import settings

# 1) Carga variables de entorno
load_dotenv()
openai.api_key    = settings.openai_api_key
twilio_auth_token = settings.twilio_auth_token

# 2) Configura logging (nivel DEBUG para ver detalles en consola)
logging.basicConfig(level=logging.DEBUG)
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
# Obtener el “cliente por defecto” (Opción 1: un solo cliente)
# ------------------------------------------------------
def get_default_client(db: Session):
    """
    Para la opción 1 (un solo cliente), devolvemos el primer registro de la tabla clients.
    """
    client = db.query(Client).first()
    if not client:
        raise HTTPException(status_code=500, detail="No hay ningún cliente registrado en BD")
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
    """
    Registra un nuevo cliente con un nombre único.
    Devuelve JSON: {id, name, api_key}.
    """
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
    db: Session   = Depends(get_db),
):
    """
    Permite al cliente subir un recurso (texto o JSON).
    En la opción 1 de pruebas, asociamos todo al primer cliente registrado.
    Body JSON: { "name": "...", "type": "...", "content": "..." }
    """
    client = get_default_client(db)

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
# Función que envía WhatsApp y guarda conversación (background)
# ------------------------------------------------------
def handle_response(user_number: str, body: str, bot_text: str, client_id: int):
    """
    Se ejecuta en segundo plano para:
      - Enviar el mensaje al usuario por WhatsApp
      - Guardar la conversación en la tabla conversations con client_id
    """
    try:
        # 1) Enviar WhatsApp
        send_message(user_number, bot_text)

        # 2) Guardar la conversación en BD
        db = SessionLocal()
        convo = Conversation(
            sender=user_number,
            message=body,
            response=bot_text,
            client_id=client_id
        )
        db.add(convo)
        db.commit()

    except Exception:
        logger.exception("Error en background task")
    finally:
        db.close()


# ------------------------------------------------------
# Endpoint /message con lógica multi-tenant básica (Opción 1)
# ------------------------------------------------------
@app.post("/message")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    request: Request,
    X_Twilio_Signature: str = Header(...),
    From: str               = Form(...),
    Body: str               = Form(...),
    db: Session             = Depends(get_db)
):
    """
    Webhook que Twilio llamará cada vez que llegue un WhatsApp.
    - Opción 1: no requerimos api_key; se usa el primer cliente.
    - Validamos la firma de Twilio.
    - Buscamos en todos los recursos JSON del cliente aquel curso cuyo nombre esté en Body.
    - Construimos el contexto con “Curso: <nombre>, Precio: $<valor>” de forma clara.
    - Llamamos a OpenAI y programamos el envío/guardado en background.
    """

    # 1) Obtener el primer cliente de la BD
    client = get_default_client(db)

    # 2) Validar la firma de Twilio
    validator = RequestValidator(twilio_auth_token)
    url       = str(request.url)
    form      = await request.form()   # <-- dentro de la función async
    if not validator.validate(url, dict(form), X_Twilio_Signature):
        logger.warning("Firma Twilio no válida")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    # 3) Extraer número de usuario (sin “whatsapp:”)
    user_number = From.replace("whatsapp:", "")

    # 4) Recuperar todos los recursos del cliente
    recursos = db.query(ClientResource).filter(ClientResource.client_id == client.id).all()
    logger.debug(f"Recursos totales del cliente {client.name}: {[r.content for r in recursos]}")

    # 5) Buscar coincidencias de “curso” dentro de Body (case-insensitive)
    contexto = ""
    encontrados = []  # Lista de cadenas formateadas para el contexto
    texto_busqueda = Body.lower()

    for r in recursos:
        try:
            lista_de_items = json.loads(r.content)
            if isinstance(lista_de_items, list):
                for item in lista_de_items:
                    # Verificamos si el nombre de curso aparece en el texto del usuario
                    nombre_curso = item.get("curso", "")
                    if nombre_curso and nombre_curso.lower() in texto_busqueda:
                        precio = item.get("precio", None)
                        if precio is not None:
                            encontrados.append(f"- Curso: {nombre_curso}, Precio: ${precio}")
                        else:
                            encontrados.append(f"- Curso: {nombre_curso}, Precio no especificado")
            else:
                # Si r.content NO es lista, lo ignoramos para esta búsqueda
                continue
        except json.JSONDecodeError:
            # Si r.content no es JSON válido, lo ignoramos en esta búsqueda
            continue

    if encontrados:
        contexto = "Información relevante para esta consulta:\n" + "\n".join(encontrados)
    logger.debug(f"Contexto a enviar a OpenAI:\n{contexto}")

    # 6) Llamar a OpenAI inyectando el contexto
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres AU Ready, un asistente virtual para AACROM University. "
                    "Responde siempre con la información que el cliente subió; "
                    "si el usuario pregunta por un curso existente, indica el precio exacto."
                )
            }
        ]

        if contexto:
            messages.append({"role": "system", "content": contexto})

        messages.append({"role": "user", "content": Body})

        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        bot_text = resp.choices[0].message.content.strip()

    except Exception:
        logger.exception("Error generando respuesta con OpenAI")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

    # 7) Programar envío y guardado en background
    background_tasks.add_task(handle_response, user_number, Body, bot_text, client.id)

    # 8) Devolver 200 OK (Twilio no necesita cuerpo)
    return ""
