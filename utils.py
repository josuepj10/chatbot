import logging
from twilio.rest import Client
from decouple import config

# Lee credenciales desde .env, usando los NOMBRES de las vars, no sus valores
account_sid   = config("TWILIO_ACCOUNT_SID")
auth_token    = config("TWILIO_AUTH_TOKEN")
twilio_number = config("TWILIO_NUMBER")    

# Inicializa Twilio
client = Client(account_sid, auth_token)

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(to_number: str, body_text: str):
    """
    Envía un WhatsApp por Twilio y loguea el resultado.
    - to_number: en formato internacional, sin "whatsapp:" (ej. "+506XXXXXXXX")
    - body_text: texto del mensaje.
    """
    try:
        message = client.messages.create(
            from_=f"whatsapp:{twilio_number}",
            to=f"whatsapp:{to_number}",
            body=body_text
        )
        logger.info(f"Message sent to {to_number}: {message.body}")
    except Exception as e:
        logger.error(f"Error sending message to {to_number}: {e}")
