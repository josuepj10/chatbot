# WhatsApp Chatbot with Twilio, FastAPI & OpenAI

A lightweight prototype of a WhatsApp chatbot using Twilio’s Sandbox, FastAPI, OpenAI’s GPT models, and PostgreSQL for message persistence.

---

## 🚀 Features

- Receives WhatsApp messages via Twilio Sandbox webhooks  
- Generates GPT-3.5-Turbo responses with OpenAI  
- Sends replies over WhatsApp via Twilio Messaging API  
- Persists each “user → bot” exchange in PostgreSQL (SQLAlchemy)  
- Validates incoming Twilio requests via `X-Twilio-Signature`  

---

## 📦 Prerequisites

- Python 3.10+  
- PostgreSQL server (local or remote)  
- Ngrok (for exposing your local FastAPI)  
- A Twilio account with WhatsApp sandbox enabled  
- OpenAI API key  

---


