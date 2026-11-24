from fastapi import Depends, HTTPException
from app.repository.user_repository import UserRepository, get_user_repository
from app.model.user_model import User
from app.schema.user_schema import (
    UserCreateDTO, UserClaimDTO, UserResponseDTO, UserUpdateDTO, UserProvider
)
from app.schema.common_schema import PageResponseDTO

from app.util.security_util import get_password_hash
import math
import os
from dotenv import load_dotenv

load_dotenv()

# 현재 시행 중인 약관 버전 (약관 개정 시 .env 또는 기본값을 변경)
TERMS_VERSION = os.getenv("TERMS_VERSION", "1.0")
HEALTH_DATA_VERSION = os.getenv("HEALTH_DATA_VERSION", "1.0")


# 예외처리, 서비스가 들어나도록 이름을 선정해서 제작
# 트랜잭션 관리
class UserService:

    def __init__(self, repo: UserRepository):
        self.repo = repo


    # 회원 가입
    # 중복 회원 검사 (이메일 + 제공자 기준). 중복이면 409
    async def check_duplicate_user(self, user_email: str, user_provider: str) -> None:
        exists_user = await self.repo.find_user_by_email_and_provider(user_email, user_provider)
        if exists_user:
            raise HTTPException(
                status_code=409,
                detail="이미 가입된 회원입니다."
            )

    # 필수 약관 동의 후 가입: users + agrees를 함께 저장
    # 동의 일시는 agrees 모델의 default(KST 현재 시각), 버전은 서버의 현재 시행 버전
    async def join(
        self, user: UserCreateDTO, agree_terms: bool, agree_health_data: bool
    ) -> UserClaimDTO:

        await self.check_duplicate_user(user.user_email, user.user_provider)
        return await self.repo.create_user(user, {
            "agree_terms_version": TERMS_VERSION,
            "agree_health_data_version": HEALTH_DATA_VERSION,
        })


    # 회원 조회(id)
    async def get_user_by_id(self, id: int):
        found_user = await self.repo.find_user_by_id(id)

        if not found_user:
            raise HTTPException(
                status_code=404,
                detail="회원이 존재하지 않습니다."
            )
        
        return UserResponseDTO.model_validate(found_user)


    # 회원 조회(email, provider)
    async def get_user_by_email_and_provider(
            self, user_email: str, user_provider: str
    ) -> User | None:
        found_user = await self.repo.find_user_by_email_and_provider(user_email, user_provider)
        
        if not found_user:
            return None

        return found_user
    

    async def update_user(self, id: int, user: UserUpdateDTO):
        exists_user = await self.repo.exists_user_by_id(id)
        if not exists_user:
            raise HTTPException(
                status_code=404,
                detail="회원을 찾을 수 없습니다",
            )

        update_data = user.model_dump(exclude_unset=True)

        response_user = await self.repo.update_user(id, update_data)

        return response_user


    # 회원 탈퇴
    async def withdraw(self, id: int):
        is_deleted = await self.repo.delete_user(id)

        if not is_deleted:
            raise HTTPException(
                status_code=404,
                detail="회원이 존재하지 않습니다"
            )


# 레포지토리 주입 팩토리 함수
def get_user_service(repo: UserRepository = Depends(get_user_repository)):
    return UserService(repo)