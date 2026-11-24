"""의료진 전용 OAuth와 임시 가입·로그인 세션. 이번 단계에서는 회원을 생성하지 않습니다."""
import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from app.repository.doctor_repository import DoctorRepository, get_doctor_repository
from app.repository.redis_repository import RedisRepository, get_redis_repository
from app.schema.doctor_auth_schema import DoctorSocialIdentityDTO, DoctorSessionDTO

load_dotenv()
FLOW_TTL = 600
PENDING_TTL = 600
SESSION_TTL = 86400
AUTH_PATH = "/doctors/auth"
SESSION_COOKIE = "doctor_session"
PENDING_COOKIE = "doctor_pending_token"
PROVIDERS = {
    "google": ("https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com/token", "https://openidconnect.googleapis.com/v1/userinfo"),
    "kakao": ("https://kauth.kakao.com/oauth/authorize", "https://kauth.kakao.com/oauth/token", "https://kapi.kakao.com/v2/user/me"),
    "naver": ("https://nid.naver.com/oauth2.0/authorize", "https://nid.naver.com/oauth2.0/token", "https://openapi.naver.com/v1/nid/me"),
}


def frontend_url() -> str:
    return os.getenv("DOCTOR_FRONTEND_URL", "http://localhost:3001").rstrip("/")


def secure_cookies() -> bool:
    return os.getenv("DOCTOR_COOKIE_SECURE", str(frontend_url().startswith("https://"))).lower() == "true"


def redis_key(kind: str, token: str) -> str:
    return f"doctor:{kind}:{hashlib.sha256(token.encode()).hexdigest()}"


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    client_id: str
    client_secret: str
    redirect_uri: str
    auth_url: str
    token_url: str
    userinfo_url: str


def provider_config(provider: str) -> ProviderConfig:
    if provider not in PROVIDERS:
        raise HTTPException(404, "지원하지 않는 소셜 로그인입니다.")
    prefix = provider.upper()
    client_id = os.getenv(f"DOCTOR_{prefix}_CLIENT_ID") or os.getenv(f"{prefix}_CLIENT_ID")
    secret = os.getenv(f"DOCTOR_{prefix}_CLIENT_SECRET") or os.getenv(f"{prefix}_CLIENT_SECRET", "")
    redirect = os.getenv(f"DOCTOR_{prefix}_REDIRECT_URI")
    if not redirect:
        # 일반 사용자 콜백 URL을 바꾸지 않고 동일 서버의 별도 경로를 사용합니다.
        existing = os.getenv(f"{prefix}_REDIRECT_URI", "")
        parts = urlsplit(existing)
        if parts.scheme and parts.netloc:
            redirect = urlunsplit((parts.scheme, parts.netloc, f"{AUTH_PATH}/{provider}/callback", "", ""))
    if not client_id or not redirect:
        raise HTTPException(503, "의료진 소셜 로그인 설정이 필요합니다.")
    return ProviderConfig(provider, client_id, secret, redirect, *PROVIDERS[provider])


class DoctorAuthService:
    def __init__(self, redis_repo: RedisRepository, doctor_repo: DoctorRepository):
        self.redis = redis_repo
        self.doctors = doctor_repo

    async def begin(self, provider: str) -> tuple[str, str]:
        config = provider_config(provider)
        state = secrets.token_urlsafe(32)
        await self.redis.set(redis_key("oauth", state), provider, ex=FLOW_TTL)
        params = {"client_id": config.client_id, "redirect_uri": config.redirect_uri,
                  "response_type": "code", "state": state}
        if provider == "google":
            params["scope"] = "openid email profile"
        return f"{config.auth_url}?{urlencode(params)}", state

    async def validate_state(self, provider: str, state: str | None, browser_state: str | None):
        if not state or not browser_state or not secrets.compare_digest(state, browser_state):
            raise HTTPException(400, "로그인 요청을 확인할 수 없습니다. 다시 로그인해 주세요.")
        # 한 번 사용한 state는 재사용하지 못하게 원자적으로 가져오고 삭제합니다.
        saved = await self.redis.getdel(redis_key("oauth", state))
        if saved != provider:
            raise HTTPException(400, "로그인 요청이 만료되었거나 이미 사용되었습니다.")

    async def exchange(self, provider: str, code: str, state: str) -> DoctorSocialIdentityDTO:
        config = provider_config(provider)
        payload = {"grant_type": "authorization_code", "code": code,
                   "client_id": config.client_id, "redirect_uri": config.redirect_uri}
        if config.client_secret:
            payload["client_secret"] = config.client_secret
        if provider == "naver":
            payload["state"] = state
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                token_response = await client.post(config.token_url, data=payload)
                token_response.raise_for_status()
                access_token = token_response.json().get("access_token")
                if not access_token:
                    raise ValueError("Missing provider token")
                user_response = await client.get(config.userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
                user_response.raise_for_status()
                user = user_response.json()
                if provider == "google":
                    provider_id, email = user.get("sub"), user.get("email")
                elif provider == "kakao":
                    provider_id, email = user.get("id"), (user.get("kakao_account") or {}).get("email")
                else:
                    profile = user.get("response") or {}
                    provider_id, email = profile.get("id"), profile.get("email")
                if provider_id is None or not str(provider_id).strip():
                    raise ValueError("Missing provider identity")
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            # 토큰·공급자 응답·개인정보를 로그나 브라우저 오류에 노출하지 않습니다.
            raise HTTPException(502, "소셜 인증 정보를 확인하지 못했습니다.") from None
        return DoctorSocialIdentityDTO(doctor_provider=provider.upper(), doctor_provider_id=str(provider_id), doctor_email=email)

    async def finish(self, identity: DoctorSocialIdentityDTO) -> tuple[str, str, str]:
        doctor = await self.doctors.find_by_provider(identity.doctor_provider, identity.doctor_provider_id)
        token = secrets.token_urlsafe(32)
        if doctor is None:
            await self.redis.set(redis_key("pending", token), identity.model_dump_json(), ex=PENDING_TTL)
            return "pending", token, "/onboarding"
        self.ensure_active(doctor)
        await self.redis.set(redis_key("session", token), str(doctor.id), ex=SESSION_TTL)
        route = "/dashboard" if doctor.doctor_verification_status else "/verification"
        return "session", token, route

    @staticmethod
    def ensure_active(doctor):
        if not doctor.doctor_status or doctor.doctor_deleted_at is not None:
            raise HTTPException(403, "이용할 수 없는 의료진 계정입니다.")

    async def pending(self, token: str | None) -> DoctorSocialIdentityDTO:
        raw = await self.redis.get(redis_key("pending", token)) if token else None
        if not raw:
            raise HTTPException(401, "추가정보 입력 시간이 만료되었습니다. 다시 로그인해 주세요.")
        return DoctorSocialIdentityDTO.model_validate_json(raw)

    async def session(self, token: str | None) -> DoctorSessionDTO:
        doctor_id = await self.redis.get(redis_key("session", token)) if token else None
        if not doctor_id:
            raise HTTPException(401, "의료진 로그인이 필요합니다.")
        doctor = await self.doctors.find_by_id(int(doctor_id))
        if doctor is None:
            raise HTTPException(401, "의료진 계정을 확인할 수 없습니다.")
        self.ensure_active(doctor)
        return DoctorSessionDTO(id=doctor.id, doctor_name=doctor.doctor_name,
            doctor_phone=doctor.doctor_phone, doctor_profession=doctor.doctor_profession,
            doctor_hospital=doctor.doctor_hospital, doctor_verification_status=doctor.doctor_verification_status,
            verification_status="APPROVED" if doctor.doctor_verification_status else "PENDING")

    async def clear(self, kind: str, token: str | None):
        if token:
            await self.redis.delete(redis_key(kind, token))


def get_doctor_auth_service(redis_repo: RedisRepository = Depends(get_redis_repository),
                            doctor_repo: DoctorRepository = Depends(get_doctor_repository)):
    return DoctorAuthService(redis_repo, doctor_repo)
