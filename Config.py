import os
from dotenv import load_dotenv
from pathlib import Path

BASEDIR = Path(__file__).resolve().parent
load_dotenv(BASEDIR / ".env")

class Config:
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash-exp")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    DB_FILE = os.getenv("DB_FILE", "/tmp/agents.db")
    MAX_QUESTIONS = 5
    MAX_CHALLENGES = 20
    
    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        if not cls.DEFAULT_MODEL:
            raise ValueError("DEFAULT_MODEL environment variable is required")