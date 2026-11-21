from pydantic import BaseModel
from datetime import datetime
from app.enum.user_enum import UserProvider, UserType

# VO (ERD 테이블: users / 회원)
class UserVO(BaseModel):
    id: int

    user_provider: UserProvider
    user_provider_id: str
    user_nickname: str
    user_phone: str
    user_status: bool
    user_created_at: datetime
    user_deleted_at: datetime | None = None
    user_type: UserType

# 토큰에 들어갈 최소한의 유저 정보
class UserClaimDTO(BaseModel):
    id: int
    user_provider: UserProvider

    class Config:
        from_attributes = True