"""머지 후 일반 회원 로그인 서비스 연결과 가입 동의 검사를 확인합니다. DB 변경 없음."""
import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from app.enum.user_enum import UserProvider
from app.schema.auth_schema import SocialLoginRequestDTO
from app.schema.user_schema import UserCreateDTO, UserClaimDTO
from app.service.auth_service import AuthService
from app.service.user_service import UserService


class UserAuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = SimpleNamespace(find_user_by_email_and_provider=AsyncMock(return_value=None),
                                    create_user=AsyncMock(return_value=UserClaimDTO(id=1, user_provider=UserProvider.GOOGLE)))
        self.users = UserService(self.repo)
        self.redis = SimpleNamespace(set=AsyncMock())
        self.auth = AuthService(self.redis, self.users)
        self.identity = SocialLoginRequestDTO(user_email="test@example.invalid", user_provider=UserProvider.GOOGLE, user_provider_id="provider-1")
        self.new_user = UserCreateDTO(user_email="test@example.invalid", user_provider=UserProvider.GOOGLE,
            user_provider_id="provider-1", user_name="검사 계정", user_nickname="검사", user_phone="01000000000")

    def test_new_social_login_returns_none_via_real_user_service(self):
        self.assertIsNone(asyncio.run(self.auth.social_login_or_none(self.identity)))
        self.repo.find_user_by_email_and_provider.assert_awaited_once_with("test@example.invalid", UserProvider.GOOGLE)
        self.redis.set.assert_not_awaited()

    def test_existing_social_login_can_issue_tokens(self):
        self.repo.find_user_by_email_and_provider.return_value = SimpleNamespace(id=1, user_email="test@example.invalid", user_provider="GOOGLE")
        with patch("app.service.auth_service.generate_access_token", return_value="test-access"), patch("app.service.auth_service.generate_refresh_token", return_value="test-refresh"):
            tokens = asyncio.run(self.auth.social_login_or_none(self.identity))
        self.assertEqual(tokens.access_token, "test-access")
        self.assertEqual(tokens.refresh_token, "test-refresh")
        self.redis.set.assert_awaited_once()

    def test_missing_required_consent_cannot_write_or_check_account(self):
        for terms, health in [(False, False), (True, False), (False, True)]:
            with self.subTest(terms=terms, health=health):
                with self.assertRaises(HTTPException) as raised:
                    asyncio.run(self.users.join(self.new_user, terms, health))
                self.assertEqual(raised.exception.status_code, 400)
        self.repo.create_user.assert_not_awaited()
        self.repo.find_user_by_email_and_provider.assert_not_awaited()

    def test_valid_consent_reaches_transactional_user_creation(self):
        result = asyncio.run(self.users.join(self.new_user, True, True))
        self.assertEqual(result.id, 1)
        args = self.repo.create_user.await_args.args
        self.assertEqual(args[0], self.new_user)
        self.assertIn("agree_terms_version", args[1])
        self.assertIn("agree_health_data_version", args[1])


if __name__ == "__main__":
    unittest.main()
