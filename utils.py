# utils.py

import logging
from twilio.rest import Client
from settings import settings

# Configura logging
def configure_logger():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

logger = configure_logger()

# Inicializa Twilio usando Pydantic Settings
twilio_client = Client(
    settings.twilio_account_sid,
    settings.twilio_auth_token
)
# Número de Twilio (sandbox o producción)
twilio_number = settings.twilio_number

def send_message(to_number: str, body_text: str) -> None:
    """
    Envía un WhatsApp por Twilio y registra el resultado en logs.

    Args:
        to_number: número destinatario en formato internacional, p.ej. "+506XXXXXXXX"
        body_text: texto del mensaje a enviar
    """
    try:
        message = twilio_client.messages.create(
            from_=f"whatsapp:{twilio_number}",
            to=f"whatsapp:{to_number}",
            body=body_text
        )
        logger.info(f"Message sent to {to_number}: {message.body}")
    except Exception as e:
        logger.error(f"Error sending message to {to_number}: {e}")
