from pydantic import BaseModel
from app.enum.user_enum import UserProvider, UserType

# DTO
class LoginRequestDTO(BaseModel):
    user_email: str
    user_provider: UserProvider | None = None

    class Config:
        from_attributes = True

        
class SocialLoginRequestDTO(BaseModel):
    user_email: str
    user_provider_id: str | None = None
    user_provider:  UserProvider | None = None

    class Config:
        from_attributes = True


class JwtTokenDTO(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None

    class Config:
        from_attributes = True


# 소셜 로그인 후 추가정보 입력 요청 (pending_token: 콜백에서 발급한 임시 키)
class SocialJoinRequestDTO(BaseModel):
    pending_token: str
    user_nickname: str
    user_phone: str
    user_type: UserType
    user_name: str

    class Config:
        from_attributes = True
