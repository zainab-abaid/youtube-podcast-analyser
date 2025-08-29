# config.py
import os
from dotenv import load_dotenv

load_dotenv()

def get_openai_model(default: str = "gpt-4o") -> str:
    return os.getenv("OPENAI_MODEL", default)

def use_whisper() -> bool:
    return os.getenv("USE_WHISPER", "false").strip().lower() in ("1", "true", "yes", "y")

def get_whisper_model(default: str = "whisper-1") -> str:
    return os.getenv("WHISPER_MODEL", default)