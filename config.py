import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    database_path: str = os.getenv("DATABASE_PATH", "data/bot.sqlite3")
    default_timeout_minutes: int = int(os.getenv("DEFAULT_TIMEOUT_MINUTES", "30"))
    elevenlabs_model_id: str = os.getenv("ELEVENLABS_MODEL_ID", "eleven_v4_turbo")
    elevenlabs_output_format: str = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")
    max_text_length: int = int(os.getenv("MAX_TEXT_LENGTH", "3000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings() 
