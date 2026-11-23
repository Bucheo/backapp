import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from jose import jwt
from app.util.jwt_token_util import (
    parse_token, generate_access_token, generate_refresh_token, reissue_access_token
)

from app.repository.redis_repository import RedisRepository, get_redis_repository
from app.repository.user_repository import UserRepository, get_user_repository
from app.enum.user_enum import UserProvider
from app.schema.user_schema import UserCreateDTO, UserClaimDTO
from app.schema.auth_schema import JwtTokenDTO, SocialJoinRequestDTO, SocialLoginRequestDTO
from app.util.jwt_token_util import parse_token, reissue_access_token
from app.service.user_service import get_user_service, UserService

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
REFRESH_TOKEN_PREFIX = os.getenv("REFRESH_TOKEN_PREFIX")
TOKEN_BLACKLIST_PREFIX = os.getenv("TOKEN_BLACKLIST_PREFIX")

# 추가정보 입력 전 임시 저장 (DB 저장 아님)
SOCIAL_PENDING_PREFIX = "social_pending:"
SOCIAL_PENDING_EX = 60 * 10  # 10분


# 예외처리
# 트랜잭션 관리
class AuthService:

    def __init__(self, redis_repo: RedisRepository, user_service: UserService):
        self.redis_repo = redis_repo
        self.user_service = user_service

    # redis에 refresh_token 저장
    # key - 콜론 체이닝
    async def save_refresh_token(self, user_id: int, refresh_token: str) -> None:
        try:
            key=f"{REFRESH_TOKEN_PREFIX}{user_id}"
            ex = 60 * 60 * 24 * 30 # 30일
            await self.redis_repo.set(key, refresh_token, ex=ex)

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="save_refresh_token 오류"
            )

    # redis에 등록된 refresh_token가 유효한지 검사
    async def validate_refresh_token(self, user_id: int, refresh_token: str) -> bool:
        key=f"{REFRESH_TOKEN_PREFIX}{user_id}"
        saved_token = await self.redis_repo.get(key)
        return refresh_token == saved_token

    # redis에 등록된 refresh_token을 삭제
    async def delete_refresh_token(self, user_id: int):
        key=f"{REFRESH_TOKEN_PREFIX}{user_id}"
        await self.redis_repo.delete(key)


    # redis에 등록된 access_token 무효화 -> 블랙리스트로 등록(로그아웃)
    async def save_blacklisted_token(self, access_token: str) -> None:
        try:
            key = f"{TOKEN_BLACKLIST_PREFIX}{access_token}"
            ex = 60 * 60 * 24

            await self.redis_repo.set(key, "blacklisted", ex=ex)

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="save_blacklisted_token 오류"
            )

    # redis에 블랙리스트로 등록되어있는지 확인
    async def is_blacklisted_token(self, access_token: str) -> bool:
        key = f"{TOKEN_BLACKLIST_PREFIX}{access_token}"
        # True -> 블랙리스트
        # False -> 사용가능
        return await self.redis_repo.exists(key)


    # 비회원 소셜 정보를 redis에 임시 저장하고 pending_token 발급 (10분)
    async def save_social_pending(self, user_params: dict) -> str:
        pending_token = secrets.token_urlsafe(32)
        await self.redis_repo.set(
            f"{SOCIAL_PENDING_PREFIX}{pending_token}",
            json.dumps(user_params),
            ex=SOCIAL_PENDING_EX,
        )
        return pending_token

    # pending_token으로 임시 저장된 소셜 정보 조회 (없거나 만료되면 None)
    async def get_social_pending(self, pending_token: str) -> dict | None:
        raw = await self.redis_repo.get(f"{SOCIAL_PENDING_PREFIX}{pending_token}")
        if raw is None:
            return None
        return json.loads(raw)

    # 가입이 끝난 뒤 임시 정보 삭제 (1회용)
    async def delete_social_pending(self, pending_token: str) -> None:
        await self.redis_repo.delete(f"{SOCIAL_PENDING_PREFIX}{pending_token}")


    async def social_login_or_none(self, social_user: SocialLoginRequestDTO) -> JwtTokenDTO | None:
        user_in_db = await self.user_service.get_user_by_email_and_provider(
            social_user.user_email,
            social_user.user_provider
        )

        if not user_in_db:
            return None

        user_id = int(user_in_db.id)
        user_email=str(user_in_db.user_email)
        user_provider=str(user_in_db.user_provider)

        claims = UserClaimDTO(
            id=user_id,
            user_email=user_email,
            user_provider=user_provider
        )

        access_token = generate_access_token(claims)
        refresh_token = generate_refresh_token(claims)
        await self.save_refresh_token(user_id, refresh_token)

        return JwtTokenDTO(
            access_token=access_token,
            refresh_token=refresh_token
        )



    # refresh_token으로 access_token 재발급
    # redis에 저장된 refresh_token과 일치해야 재발급한다
    async def refresh(self, refresh_token: str) -> str:
        claims = parse_token(refresh_token)

        if not await self.validate_refresh_token(claims.id, refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 refresh_token 입니다."
            )

        return generate_access_token(claims)


    # 로그아웃: access_token 블랙리스트 등록 + refresh_token 삭제
    async def logout(self, user_id: int, tokens: JwtTokenDTO) -> None:
        if tokens.access_token:
            await self.save_blacklisted_token(tokens.access_token)

        await self.delete_refresh_token(user_id)



# 레포지토리 주입 팩토리 함수
def get_auth_service(
    redis_repo: RedisRepository = Depends(get_redis_repository),
    user_repo: UserService = Depends(get_user_service)
):
    return AuthService(redis_repo, user_repo)
