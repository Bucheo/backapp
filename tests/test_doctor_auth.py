"""의료진 OAuth·세션 회귀 검사. 실제 OAuth 서버, Redis, DB는 사용하거나 수정하지 않습니다."""
import json
import asyncio
import httpx
import unittest
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import configure_mappers
from app.api.doctor_auth_api import router
from app.service.doctor_auth_service import DoctorAuthService, get_doctor_auth_service, redis_key, AUTH_PATH
from app.schema.doctor_auth_schema import DoctorSocialIdentityDTO
from app.model.doctor_model import Doctor
from app.model.user_model import User


class MemoryRedis:
    def __init__(self):
        self.values = {}
        self.ttls = {}

    async def set(self, key, value, ex=3600):
        self.values[key] = value
        self.ttls[key] = ex

    async def get(self, key):
        return self.values.get(key)

    async def getdel(self, key):
        return self.values.pop(key, None)

    async def delete(self, key):
        self.values.pop(key, None)


class DoctorAuthTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict("os.environ", {
            "DOCTOR_FRONTEND_URL": "http://localhost:3001", "DOCTOR_COOKIE_SECURE": "false",
            **{f"DOCTOR_{name}_CLIENT_ID": "test-client" for name in ["GOOGLE", "KAKAO", "NAVER"]},
            **{f"DOCTOR_{name}_CLIENT_SECRET": "test-secret" for name in ["GOOGLE", "KAKAO", "NAVER"]},
            **{f"DOCTOR_{name}_REDIRECT_URI": f"http://testserver/doctors/auth/{name.lower()}/callback" for name in ["GOOGLE", "KAKAO", "NAVER"]},
        })
        self.env.start()
        self.redis = MemoryRedis()
        self.doctor = SimpleNamespace(id=7, doctor_name="검사 계정", doctor_phone="010-0000-0000",
            doctor_profession="의사", doctor_hospital="검사용 병원", doctor_status=True,
            doctor_deleted_at=None, doctor_verification_status=True)
        self.repo = SimpleNamespace(find_by_provider=AsyncMock(return_value=None),
                                    find_by_id=AsyncMock(return_value=self.doctor))
        self.service = DoctorAuthService(self.redis, self.repo)
        self.service.exchange = AsyncMock(return_value=DoctorSocialIdentityDTO(
            doctor_provider="GOOGLE", doctor_provider_id="social-7", doctor_email="test@example.invalid"))
        self.app = FastAPI()
        self.app.include_router(router, prefix=AUTH_PATH)
        self.app.dependency_overrides[get_doctor_auth_service] = lambda: self.service
        self.client = TestClient(self.app, follow_redirects=False)

    def tearDown(self):
        self.client.close()
        self.env.stop()

    def start(self, provider="google"):
        response = self.client.get(f"{AUTH_PATH}/{provider}")
        self.assertEqual(response.status_code, 302)
        state = parse_qs(urlsplit(response.headers["location"]).query)["state"][0]
        return state, response

    def callback(self, state, provider="google", **params):
        return self.client.get(f"{AUTH_PATH}/{provider}/callback", params={"state": state, "code": "test-code", **params})

    def test_each_provider_uses_isolated_callback_and_bound_state(self):
        for provider in ["google", "kakao", "naver"]:
            state, response = self.start(provider)
            query = parse_qs(urlsplit(response.headers["location"]).query)
            self.assertEqual(query["redirect_uri"], [f"http://testserver/doctors/auth/{provider}/callback"])
            self.assertIn("HttpOnly", response.headers["set-cookie"])
            self.assertIn("SameSite=lax", response.headers["set-cookie"])
            self.assertEqual(self.redis.values[redis_key("oauth", state)], provider)

    def test_new_doctor_is_only_pending_without_database_insert(self):
        state, _ = self.start()
        response = self.callback(state)
        self.assertEqual(response.headers["location"], "http://localhost:3001/onboarding")
        self.assertNotIn("pending_token=", response.headers["location"])
        self.assertNotIn("email=", response.headers["location"])
        pending = self.client.get(AUTH_PATH + "/pending")
        self.assertEqual(pending.status_code, 200)
        self.assertEqual(pending.json()["data"]["doctor_provider_id"], "social-7")
        self.repo.find_by_provider.assert_awaited_once_with("GOOGLE", "social-7")
        self.assertEqual(self.client.get(AUTH_PATH + "/session").status_code, 401)
        keys = [k for k in self.redis.values if k.startswith("doctor:pending:")]
        self.assertEqual(len(keys), 1)
        self.assertEqual(self.redis.ttls[keys[0]], 600)

    def test_approved_doctor_redirects_dashboard_with_real_session(self):
        self.repo.find_by_provider.return_value = self.doctor
        state, _ = self.start()
        response = self.callback(state)
        self.assertEqual(response.headers["location"], "http://localhost:3001/dashboard")
        session = self.client.get(AUTH_PATH + "/session")
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json()["data"]["id"], 7)
        self.assertEqual(session.json()["data"]["verification_status"], "APPROVED")
        self.assertEqual(session.headers["cache-control"], "no-store")

    def test_pending_doctor_redirects_verification_and_status_is_read_again(self):
        self.repo.find_by_provider.return_value = self.doctor
        self.doctor.doctor_verification_status = False
        state, _ = self.start()
        self.assertTrue(self.callback(state).headers["location"].endswith("/verification"))
        self.assertEqual(self.client.get(AUTH_PATH + "/session").json()["data"]["verification_status"], "PENDING")
        self.doctor.doctor_verification_status = True
        self.assertEqual(self.client.get(AUTH_PATH + "/session").json()["data"]["verification_status"], "APPROVED")

    def test_state_mismatch_and_replay_never_exchange_code(self):
        state, _ = self.start()
        self.assertIn("error=login_failed", self.callback("wrong-state").headers["location"])
        self.service.exchange.assert_not_awaited()
        state, _ = self.start()
        self.callback(state)
        self.callback(state)
        self.assertEqual(self.service.exchange.await_count, 1)

    def test_state_cannot_move_between_providers(self):
        state, _ = self.start("google")
        response = self.callback(state, "kakao")
        self.assertIn("error=login_failed", response.headers["location"])
        self.service.exchange.assert_not_awaited()

    def test_expired_state_and_pending_are_rejected(self):
        state, _ = self.start()
        self.redis.values.clear()
        self.assertIn("error=login_failed", self.callback(state).headers["location"])
        self.assertEqual(self.client.get(AUTH_PATH + "/pending").status_code, 401)
        self.service.exchange.assert_not_awaited()

    def test_provider_cancel_does_not_create_pending_or_session(self):
        state, _ = self.start()
        response = self.callback(state, error="access_denied")
        self.assertIn("error=cancelled", response.headers["location"])
        self.service.exchange.assert_not_awaited()
        self.assertFalse(self.redis.values)

    def test_disabled_doctor_cannot_login(self):
        self.repo.find_by_provider.return_value = self.doctor
        self.doctor.doctor_status = False
        state, _ = self.start()
        self.assertIn("error=account_disabled", self.callback(state).headers["location"])
        self.assertEqual(self.client.get(AUTH_PATH + "/session").status_code, 401)

    def test_general_member_cookie_is_not_doctor_auth(self):
        self.client.cookies.set("access_token", "user-token")
        self.client.cookies.set("refresh_token", "user-refresh")
        self.assertEqual(self.client.get(AUTH_PATH + "/session").status_code, 401)
        self.assertEqual(self.client.get(AUTH_PATH + "/pending").status_code, 401)

    def test_cancel_pending_revokes_token_and_checks_origin(self):
        state, _ = self.start()
        self.callback(state)
        self.assertEqual(self.client.post(AUTH_PATH + "/pending/cancel", headers={"Origin": "http://untrusted.invalid"}).status_code, 403)
        self.assertEqual(self.client.get(AUTH_PATH + "/pending").status_code, 200)
        self.assertEqual(self.client.post(AUTH_PATH + "/pending/cancel", headers={"Origin": "http://localhost:3001"}).status_code, 200)
        self.assertEqual(self.client.get(AUTH_PATH + "/pending").status_code, 401)

    def test_logout_revokes_server_session(self):
        self.repo.find_by_provider.return_value = self.doctor
        state, _ = self.start()
        self.callback(state)
        self.assertEqual(self.client.post(AUTH_PATH + "/logout", headers={"Origin": "http://localhost:3001"}).status_code, 200)
        self.assertEqual(self.client.get(AUTH_PATH + "/session").status_code, 401)

    def test_real_exchange_parses_each_provider_response(self):
        client_type = httpx.AsyncClient
        for provider, profile in [
            ("google", {"sub": "google-id", "email": "test@example.invalid"}),
            ("kakao", {"id": 123, "kakao_account": {}}),
            ("naver", {"response": {"id": "naver-id", "email": "test@example.invalid"}}),
        ]:
            calls = []
            def handle(request):
                calls.append(request)
                return httpx.Response(200, json={"access_token": "provider-only-token"} if request.method == "POST" else profile)
            with patch("app.service.doctor_auth_service.httpx.AsyncClient", return_value=client_type(transport=httpx.MockTransport(handle))):
                identity = asyncio.run(DoctorAuthService(self.redis, self.repo).exchange(provider, "test-code", "test-state"))
            self.assertEqual(identity.doctor_provider, provider.upper())
            self.assertEqual(calls[1].headers["authorization"], "Bearer provider-only-token")
            values = parse_qs(calls[0].content.decode())
            self.assertEqual(values["redirect_uri"], [f"http://testserver/doctors/auth/{provider}/callback"])
            if provider == "naver":
                self.assertEqual(values["state"], ["test-state"])
            if provider == "kakao":
                self.assertIsNone(identity.doctor_email)

    def test_failed_provider_token_is_not_accepted(self):
        from fastapi import HTTPException
        client_type = httpx.AsyncClient
        with patch("app.service.doctor_auth_service.httpx.AsyncClient", return_value=client_type(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"error": "invalid_grant"})))):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(DoctorAuthService(self.redis, self.repo).exchange("google", "bad", "state"))
            self.assertEqual(raised.exception.status_code, 502)

    def test_cors_explicitly_allows_doctor_frontend_credentials(self):
        from app.security.cors import setup_cors
        setup_cors(self.app)
        response = self.client.get(AUTH_PATH + "/session", headers={"Origin": "http://localhost:3001"})
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3001")
        self.assertEqual(response.headers["access-control-allow-credentials"], "true")

    def test_orm_doctor_is_separate_from_general_user(self):
        configure_mappers()
        self.assertNotIn("user_id", Doctor.__table__.columns)
        self.assertNotIn("doctors", User.__mapper__.relationships)


if __name__ == "__main__":
    unittest.main()
