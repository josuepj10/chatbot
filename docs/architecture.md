# Arquitectura de Alto Nivel

```mermaid
flowchart LR
  User[Usuario WhatsApp] -->|envía mensaje| Twilio(Twilio Sandbox)
  Twilio -->|POST /message| FastAPI[FastAPI Webhook]
  FastAPI --> OpenAI[OpenAI API]
  FastAPI -->|BackgroundTask| Utils(send_message + DB)
  Utils --> Twilio
  Utils --> PostgreSQL[(PostgreSQL)]
