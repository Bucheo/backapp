from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: agrees / 약관 동의)
class AgreeVO(BaseModel):
    agree_terms_agreed_at: datetime
    agree_terms_version: str
    agree_health_data_agreed_at: datetime
    agree_health_data_version: str

    user_id: int