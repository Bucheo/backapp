import os
import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.enum.user_enum import UserProvider
from app.schema.auth_schema import JwtTokenDTO, SocialJoinRequestDTO
from app.schema.common_schema import ApiResponseDTO
from app.service.auth_service import AuthService, get_auth_service

load_dotenv()
router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL")

# provider별 OAuth 설정 (.env)
SOCIAL_PROVIDERS = {
    UserProvider.GOOGLE: {
        "auth_url": os.getenv("GOOGLE_AUTH_URL"),
        "token_url": os.getenv("GOOGLE_TOKEN_URL"),
        "userinfo_url": os.getenv("GOOGLE_USERINFO_URL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "scope": "openid profile",
    },
    UserProvider.KAKAO: {
        "auth_url": os.getenv("KAKAO_AUTH_URL"),
        "token_url": os.getenv("KAKAO_TOKEN_URL"),
        "userinfo_url": os.getenv("KAKAO_USERINFO_URL"),
        "client_id": os.getenv("KAKAO_CLIENT_ID"),
        "client_secret": os.getenv("KAKAO_CLIENT_SECRET"),
        "redirect_uri": os.getenv("KAKAO_REDIRECT_URI"),
        "scope": None,
    },
    UserProvider.NAVER: {
        "auth_url": os.getenv("NAVER_AUTH_URL"),
        "token_url": os.getenv("NAVER_TOKEN_URL"),
        "userinfo_url": os.getenv("NAVER_USERINFO_URL"),
        "client_id": os.getenv("NAVER_CLIENT_ID"),
        "client_secret": os.getenv("NAVER_CLIENT_SECRET"),
        "redirect_uri": os.getenv("NAVER_REDIRECT_URI"),
        "scope": None,
    },
}


# provider별 사용자 응답에서 제공자 고유 id 꺼내기
def _extract_provider_id(user_provider: UserProvider, user_info: dict) -> str:
    if user_provider == UserProvider.GOOGLE:
        return str(user_info["sub"])
    if user_provider == UserProvider.KAKAO:
        return str(user_info["id"])
    if user_provider == UserProvider.NAVER:
        return str(user_info["response"]["id"])
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지원하지 않는 provider")


# code -> access_token -> 사용자 정보 -> provider_id
async def _get_provider_id(user_provider: UserProvider, code: str) -> str:
    config = SOCIAL_PROVIDERS[user_provider]

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            config["token_url"],
            data={
                "code": code,
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "redirect_uri": config["redirect_uri"],
                "grant_type": "authorization_code"
            }
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="소셜 토큰 발급 실패")

        access_token = token_res.json().get("access_token")

        user_res = await client.get(
            config["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_res.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="소셜 사용자 정보 조회 실패")

    return _extract_provider_id(user_provider, user_res.json())


# 쿠키 설정
def _set_auth_cookies(response: Response, tokens: JwtTokenDTO) -> None:
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 30
    )


# 1. 소셜 로그인 시작 -> 제공자 로그인 페이지로 리다이렉트
# GET /auth/social/{provider}
@router.get("/social/{user_provider}", summary="소셜 로그인 리다이렉트")
async def social_login(user_provider: UserProvider):
    config = SOCIAL_PROVIDERS[user_provider]

    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
    }
    if config["scope"]:
        params["scope"] = config["scope"]

    url = f"{config['auth_url']}?{urlencode(params)}"
    return RedirectResponse(url)


# 2. 소셜 로그인 콜백 -> 기존 회원이면 로그인, 신규 회원이면 추가정보 입력 페이지로
# GET /auth/social/{provider}/callback
@router.get("/social/{user_provider}/callback", summary="소셜 로그인 콜백")
async def social_login_callback(
    user_provider: UserProvider,
    code: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    provider_id = await _get_provider_id(user_provider, code)

    tokens = await auth_service.social_login_or_none(user_provider, provider_id)

    # 기존 회원 -> 토큰 발급 후 프론트로
    if tokens:
        redirect_response = RedirectResponse(url=FRONTEND_URL)
        _set_auth_cookies(redirect_response, tokens)
        return redirect_response

    # 신규 회원 -> DB 저장 없이 임시 키만 발급 후 추가정보 입력 페이지로
    pending_token = await auth_service.save_pending_social_user(user_provider, provider_id)
    query = urlencode({"pending_token": pending_token})
    return RedirectResponse(url=f"{FRONTEND_URL}/join-additional?{query}")


# 3. 추가정보 입력 후 최초 가입 -> 토큰 발급
# POST /auth/social/join
@router.post(
    "/social/join",
    response_model=ApiResponseDTO,
    summary="소셜 회원가입 (추가정보 입력)"
)
async def social_join(
    join_request: SocialJoinRequestDTO,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.join_social_user(join_request)
    _set_auth_cookies(response, tokens)

    return ApiResponseDTO(
        success=True,
        message="회원가입 성공"
    )
