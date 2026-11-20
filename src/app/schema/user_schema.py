from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: users / 회원)
class UserVO(BaseModel):
    id: int

    user_provider: str
    user_provider_id: str
    user_nickname: str
    user_phone: str
    user_status: str
    user_created_at: datetime
    user_deleted_at: datetime | None = None
    user_type: str
