import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from jose import jwt

from app.repository.redis_repository import RedisRepository, get_redis_repository
from app.repository.user_repository import UserRepository, get_user_repository
from app.enum.user_enum import UserProvider
from app.schema.user_schema import UserCreateDTO, UserClaimDTO
from app.schema.auth_schema import JwtTokenDTO, SocialJoinRequestDTO

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
REFRESH_TOKEN_PREFIX = os.getenv("REFRESH_TOKEN_PREFIX")

# 추가정보 입력 전 임시 저장 (DB 저장 아님)
SOCIAL_PENDING_PREFIX = "social_pending:"
SOCIAL_PENDING_EX = 60 * 10  # 10분


# 예외처리
# 트랜잭션 관리
class AuthService:

    def __init__(self, redis_repo: RedisRepository, user_repo: UserRepository):
        self.redis_repo = redis_repo
        self.user_repo = user_repo


    # JWT 생성
    def _create_token(self, claims: UserClaimDTO, expire_delta: timedelta) -> str:
        payload = claims.model_dump(mode="json")
        payload["exp"] = datetime.now(timezone.utc) + expire_delta
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


    # access / refresh 발급 + refresh는 redis에 저장
    async def _issue_tokens(self, user_id: int, user_provider: UserProvider) -> JwtTokenDTO:
        claims = UserClaimDTO(id=user_id, user_provider=user_provider)

        access_token = self._create_token(claims, timedelta(days=1))
        refresh_token = self._create_token(claims, timedelta(days=30))

        await self.redis_repo.set(
            f"{REFRESH_TOKEN_PREFIX}{user_id}",
            refresh_token,
            ex=60 * 60 * 24 * 30
        )

        return JwtTokenDTO(
            access_token=access_token,
            refresh_token=refresh_token
        )


    # 1. 기존 회원이면 토큰 발급, 신규 회원이면 None
    async def social_login_or_none(self, user_provider: UserProvider, user_provider_id: str) -> JwtTokenDTO | None:
        found_user = await self.user_repo.find_user_by_provider(user_provider.value, user_provider_id)

        if not found_user:
            return None

        return await self._issue_tokens(found_user.id, UserProvider(found_user.user_provider))


    # 2. 신규 회원: DB에 넣지 않고 provider 정보를 임시 키로 redis에 저장
    async def save_pending_social_user(self, user_provider: UserProvider, user_provider_id: str) -> str:
        pending_token = secrets.token_urlsafe(32)
        value = json.dumps({
            "user_provider": user_provider.value,
            "user_provider_id": user_provider_id
        })

        await self.redis_repo.set(
            f"{SOCIAL_PENDING_PREFIX}{pending_token}",
            value,
            ex=SOCIAL_PENDING_EX
        )
        return pending_token


    # 3. 추가정보 입력 후 최초 가입 (DB 저장 -> 토큰 발급)
    async def join_social_user(self, join_dto: SocialJoinRequestDTO) -> JwtTokenDTO:
        key = f"{SOCIAL_PENDING_PREFIX}{join_dto.pending_token}"

        raw = await self.redis_repo.get(key)
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="가입 세션이 만료되었습니다."
            )

        pending = json.loads(raw)
        user_provider = UserProvider(pending["user_provider"])
        user_provider_id = pending["user_provider_id"]

        # 중복 가입 방지
        if await self.user_repo.find_user_by_provider(user_provider.value, user_provider_id):
            await self.redis_repo.delete(key)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 가입된 회원입니다."
            )

        new_user = UserCreateDTO(
            user_provider=user_provider,
            user_provider_id=user_provider_id,
            user_nickname=join_dto.user_nickname,
            user_phone=join_dto.user_phone,
            user_type=join_dto.user_type
        )

        claims = await self.user_repo.create_user(new_user)
        await self.redis_repo.delete(key)

        return await self._issue_tokens(claims.id, claims.user_provider)


# 레포지토리 주입 팩토리 함수
def get_auth_service(
    redis_repo: RedisRepository = Depends(get_redis_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    return AuthService(redis_repo, user_repo)
