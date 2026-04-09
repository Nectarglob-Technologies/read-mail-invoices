from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    TENANT_ID: str | None = None
    CLIENT_ID: str | None = None
    CLIENT_SECRET: str | None = None
    OUTLOOK_USER: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()

OPENAI_API_KEY =  os.getenv("OPENAI_API_KEY") # 🔥 replace
LLM_MODEL = "gpt-5-mini"


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
OUTPUT_DIR = os.path.join(DATA_DIR, "output_json")

for path in [ATTACHMENTS_DIR, IMAGES_DIR, OUTPUT_DIR]:
    os.makedirs(path, exist_ok=True)
