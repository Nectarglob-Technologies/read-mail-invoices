from pydantic_settings import BaseSettings
import os

#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4o-mini"
    TENANT_ID: str | None = None
    CLIENT_ID: str | None = None
    CLIENT_SECRET: str | None = None
    OUTLOOK_USER: str | None = None

    class Config:
        #env_file = os.path.join(BASE_DIR, ".env")   # ✅ FIXED
        env_file = ".env"   # ✅ FIXED
        
settings = Settings()

OPENAI_API_KEY = settings.OPENAI_API_KEY
LLM_MODEL = settings.LLM_MODEL

#OPENAI_API_KEY =  os.getenv("OPENAI_API_KEY") # 🔥 replace
#LLM_MODEL = os.getenv("LLM_MODEL") 


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
OUTPUT_DIR = os.path.join(DATA_DIR, "output_json")

for path in [ATTACHMENTS_DIR, IMAGES_DIR, OUTPUT_DIR]:
    os.makedirs(path, exist_ok=True)
