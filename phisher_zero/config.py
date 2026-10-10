import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    VIRUSTOTAL_API_KEY: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    
    # Ensemble Weights
    URL_WEIGHT: float = 0.10
    NLP_WEIGHT: float = 0.60
    VIRUSTOTAL_WEIGHT: float = 0.30
    
    # Thresholds
    PHISHING_THRESHOLD: float = 0.70
    SUSPICIOUS_THRESHOLD: float = 0.40
    
    # Models
    HF_NLP_MODEL: str = "cybersectony/phishing-email-detection-distilbert_v2.4.1"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
