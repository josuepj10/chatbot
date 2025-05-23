# settings.py

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Twilio
    twilio_account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")
    twilio_number: str     = Field(..., env="TWILIO_NUMBER")

    # OpenAI
    openai_api_key: str     = Field(..., env="OPENAI_API_KEY")

    # Base de datos
    db_user: str            = Field(..., env="DB_USER")
    db_password: str        = Field(..., env="DB_PASSWORD")
    db_host: str            = Field("localhost", env="DB_HOST")
    db_port: int            = Field(5432, env="DB_PORT")
    db_name: str            = Field(..., env="DB_NAME")

    # Whatsapp destino (opcional)
    to_number: str          = Field(..., env="TO_NUMBER")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
