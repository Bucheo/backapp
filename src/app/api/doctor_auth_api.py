from urllib.parse import urlsplit
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from app.schema.common_schema import ApiResponseDTO
from app.schema.doctor_auth_schema import DoctorProviderName, DoctorSessionDTO, DoctorSocialIdentityDTO
from app.service.doctor_auth_service import (
    AUTH_PATH, FLOW_TTL, PENDING_TTL, SESSION_TTL, SESSION_COOKIE, PENDING_COOKIE,
    DoctorAuthService, get_doctor_auth_service, frontend_url, secure_cookies,
)

router = APIRouter()


def set_cookie(response, name: str, token: str, max_age: int, path: str = AUTH_PATH):
    response.set_cookie(name, token, max_age=max_age, path=path,
                        httponly=True, secure=secure_cookies(), samesite="lax")


def clear_cookie(response, name: str, path: str = AUTH_PATH):
    response.delete_cookie(name, path=path, httponly=True, secure=secure_cookies(), samesite="lax")


def no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def check_origin(request: Request):
    parts = urlsplit(frontend_url())
    if request.headers.get("origin") != f"{parts.scheme}://{parts.netloc}":
        raise HTTPException(403, "허용되지 않은 요청입니다.")


@router.get("/session", response_model=ApiResponseDTO[DoctorSessionDTO])
async def session(request: Request, service: DoctorAuthService = Depends(get_doctor_auth_service)):
    profile = await service.session(request.cookies.get(SESSION_COOKIE))
    return no_store(JSONResponse(ApiResponseDTO(success=True, message="의료진 로그인 확인", data=profile).model_dump(mode="json")))


@router.get("/pending", response_model=ApiResponseDTO[DoctorSocialIdentityDTO])
async def pending(request: Request, service: DoctorAuthService = Depends(get_doctor_auth_service)):
    identity = await service.pending(request.cookies.get(PENDING_COOKIE))
    return no_store(JSONResponse(ApiResponseDTO(success=True, message="의료진 소셜 인증 확인", data=identity).model_dump(mode="json")))


@router.post("/pending/cancel")
async def cancel_pending(request: Request, service: DoctorAuthService = Depends(get_doctor_auth_service)):
    check_origin(request)
    await service.clear("pending", request.cookies.get(PENDING_COOKIE))
    response = JSONResponse(ApiResponseDTO(success=True, message="추가정보 입력 취소").model_dump(mode="json"))
    clear_cookie(response, PENDING_COOKIE)
    return no_store(response)


@router.post("/logout")
async def logout(request: Request, service: DoctorAuthService = Depends(get_doctor_auth_service)):
    check_origin(request)
    await service.clear("session", request.cookies.get(SESSION_COOKIE))
    response = JSONResponse(ApiResponseDTO(success=True, message="의료진 로그아웃").model_dump(mode="json"))
    clear_cookie(response, SESSION_COOKIE)
    return no_store(response)


@router.get("/{provider}")
async def login(provider: DoctorProviderName, service: DoctorAuthService = Depends(get_doctor_auth_service)):
    url, state = await service.begin(provider)
    response = RedirectResponse(url, status_code=302)
    set_cookie(response, f"doctor_oauth_state_{provider}", state, FLOW_TTL, f"{AUTH_PATH}/{provider}")
    return no_store(response)


@router.get("/{provider}/callback")
async def callback(provider: DoctorProviderName, request: Request, code: str | None = None,
                   state: str | None = None, error: str | None = None,
                   service: DoctorAuthService = Depends(get_doctor_auth_service)):
    cookie_name = f"doctor_oauth_state_{provider}"
    try:
        await service.validate_state(provider, state, request.cookies.get(cookie_name))
        if error or not code:
            response = RedirectResponse(f"{frontend_url()}/login?error=cancelled", status_code=302)
        else:
            identity = await service.exchange(provider, code, state)
            kind, token, route = await service.finish(identity)
            response = RedirectResponse(frontend_url() + route, status_code=302)
            # 새 인증으로 로그인 대상이 바뀌면 이전 계정 세션/임시정보는 폐기합니다.
            await service.clear("pending", request.cookies.get(PENDING_COOKIE))
            await service.clear("session", request.cookies.get(SESSION_COOKIE))
            clear_cookie(response, SESSION_COOKIE)
            clear_cookie(response, PENDING_COOKIE)
            if kind == "pending":
                set_cookie(response, PENDING_COOKIE, token, PENDING_TTL)
            else:
                set_cookie(response, SESSION_COOKIE, token, SESSION_TTL)
    except HTTPException as exc:
        error_code = "account_disabled" if exc.status_code == 403 else "login_failed"
        response = RedirectResponse(f"{frontend_url()}/login?error={error_code}", status_code=302)
    clear_cookie(response, cookie_name, f"{AUTH_PATH}/{provider}")
    return no_store(response)
