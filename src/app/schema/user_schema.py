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


# DTO
# 1. 소셜 로그인 후 추가정보 입력 시 받는 값 -> 이 값으로 최초 가입(DB 저장)
class UserCreateDTO(BaseModel):
    user_provider: UserProvider
    user_provider_id: str
    user_nickname: str
    user_phone: str
    user_type: UserType

    class Config:
        from_attributes = True


# 2. 회원 정보 수정
class UserUpdateDTO(BaseModel):
    user_nickname: str | None = None
    user_phone: str | None = None

    class Config:
        from_attributes = True


# 3. 회원 정보 응답
class UserResponseDTO(BaseModel):
    id: int
    user_provider: UserProvider
    user_provider_id: str
    user_nickname: str
    user_phone: str
    user_status: bool
    user_created_at: datetime
    user_type: UserType

    class Config:
        from_attributes = True


# 토큰에 들어갈 최소한의 유저 정보
class UserClaimDTO(BaseModel):
    id: int
    user_provider: UserProvider

    class Config:
        from_attributes = True