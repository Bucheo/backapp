import os
import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.enum.user_enum import UserProvider
from app.schema.auth_schema import JwtTokenDTO, SocialJoinRequestDTO
from app.schema.common_schema import ApiResponseDTO
from app.schema.user_schema import UserClaimDTO
from app.service.auth_service import AuthService, get_auth_service
from app.dependency.auth_dependency import get_current_member, get_tokens

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


# 제공자 로그인 페이지로 리다이렉트
def _redirect_to_provider(user_provider: UserProvider) -> RedirectResponse:
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


# 콜백 공통 처리 -> 기존 회원이면 로그인, 신규 회원이면 추가정보 입력 페이지로
async def _handle_callback(user_provider: UserProvider, code: str, auth_service: AuthService):
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


# ---------- 구글 ----------
# GET /auth/google
@router.get("/google", summary="구글 로그인")
async def google_login():
    return _redirect_to_provider(UserProvider.GOOGLE)


# GET /auth/google/callback
@router.get("/google/callback", summary="구글 로그인 콜백")
async def google_login_callback(
    code: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await _handle_callback(UserProvider.GOOGLE, code, auth_service)


# ---------- 카카오 ----------
# GET /auth/kakao
@router.get("/kakao", summary="카카오 로그인 리다이렉트")
async def kakao_login():
    return _redirect_to_provider(UserProvider.KAKAO)


# GET /auth/kakao/callback
@router.get("/kakao/callback", summary="카카오 로그인 콜백")
async def kakao_login_callback(
    code: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await _handle_callback(UserProvider.KAKAO, code, auth_service)


# ---------- 네이버 ----------
# GET /auth/naver
@router.get("/naver", summary="네이버 로그인 리다이렉트")
async def naver_login():
    return _redirect_to_provider(UserProvider.NAVER)


# GET /auth/naver/callback
@router.get("/naver/callback", summary="네이버 로그인 콜백")
async def naver_login_callback(
    code: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await _handle_callback(UserProvider.NAVER, code, auth_service)


# ---------- 추가정보 입력 ----------
# 추가정보 입력 후 최초 가입 -> 토큰 발급
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


# ---------- 로그아웃 / 토큰 재발급 ----------
# 로그아웃: access_token 블랙리스트 + refresh_token 삭제 + 쿠키 제거
# POST /auth/logout
@router.post(
    "/logout",
    response_model=ApiResponseDTO,
    summary="로그아웃"
)
async def logout(
    response: Response,
    user_claims: UserClaimDTO = Depends(get_current_member),
    tokens: JwtTokenDTO = Depends(get_tokens),
    auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.logout(user_claims.id, tokens)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return ApiResponseDTO(
        success=True,
        message="로그아웃 성공"
    )


# 토큰 재발급: refresh_token 쿠키로 access_token 재발급
# GET /auth/refresh
@router.get(
    "/refresh",
    response_model=ApiResponseDTO,
    summary="토큰 재발급"
)
async def refresh(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    # access_token이 만료돼도 재발급은 가능해야 하므로 refresh_token 쿠키를 직접 읽는다
    refresh_token = request.cookies.get("refresh_token")

    try:
        access_token = await auth_service.refresh(refresh_token)

    except HTTPException:
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return ApiResponseDTO(
            success=False,
            message="Refresh Token 만료"
        )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24
    )

    return ApiResponseDTO(
        success=True,
        message="Access Token 재발급 성공"
    )
