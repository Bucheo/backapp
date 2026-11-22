from fastapi import Depends, HTTPException
from app.repository.user_repository import UserRepository, get_user_repository
from app.model.user_model import User
from app.schema.user_schema import (
    UserCreateDTO, UserClaimDTO, UserResponseDTO, UserUpdateDTO, UserProvider
)
from app.schema.common_schema import PageResponseDTO

from app.util.security_util import get_password_hash
import math


# 예외처리, 서비스가 들어나도록 이름을 선정해서 제작
# 트랜잭션 관리
class UserService:

    def __init__(self, repo: UserRepository):
        self.repo = repo


    # 회원 가입
    async def join(self, user: UserCreateDTO) -> UserClaimDTO:
        await self.check_duplicate_user(user.user_email, user.user_provider)



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