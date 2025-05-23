# Chatbot de WhatsApp con FastAPI, Twilio y OpenAI

Este repositorio contiene un **prototipo funcional** de un chatbot de WhatsApp que utiliza:
- **FastAPI** (web framework)
- **Twilio Sandbox para WhatsApp** (mensajería)
- **OpenAI** (generación de lenguaje)
- **PostgreSQL + Alembic** (persistencia y migraciones)
- **Pydantic Settings** (gestión de configuración)
- **BackgroundTasks** de FastAPI (envío y persistencia off-thread)

### 🚀 Quickstart

1. Clona este repo:
   ```bash
   git clone 
   cd chatbot

2. Crea y activa el entorno: 
python -m venv venv
source venv/bin/activate    # o .\venv\Scripts\activate.bat en Windows
pip install -r requirements.txt

3. Copia .env.example a .env y rellena tus credenciales:

dotenv
Copy
Edit
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_NUMBER=+14155238886
OPENAI_API_KEY=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatbot
TO_NUMBER=+506XXXXXXXX

4. Prepara la base de datos y aplica migraciones:

bash
Copy
Edit
createdb chatbot
alembic upgrade head

5. Levanta el servidor y ngrok:

bash
Copy
Edit
uvicorn main:app --reload
ngrok http 8000

6. Configura el webhook en Twilio Sandbox (URL_ngrok/message) y envía “join <código>” a +1 415 523 8886.

¡Envía mensajes por WhatsApp y recibe respuestas de GPT!






