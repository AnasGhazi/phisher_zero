from pydantic import BaseModel

class PhishResult(BaseModel):
    is_phishing: int      # 1 or 0
    reason: str
