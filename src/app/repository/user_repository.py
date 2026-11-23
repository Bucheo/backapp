from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.postgresql import get_postgresql_db
from fastapi import Depends

# 모델, ORM
from app.model.user_model import User
from app.schema.user_schema import UserCreateDTO, UserClaimDTO
from sqlalchemy import insert, select, update, delete, func, exists  # CRUD 순서


class UserRepository:

    # 생성자 주입
    def __init__(self, db: AsyncSession):
        self.db = db


    # 순수 함수
    # 회원가입
    async def create_user(self, user: UserCreateDTO):
        # pydantic -> dict
        new_user = user.model_dump()
        query = (
            insert(User)
            .values(**new_user)
        ).returning(
            User.id,
            User.user_email,
            User.user_provider
        )

        result = await self.db.execute(query)

        # 필요한 값을 리턴(id, email, provider)
        id, user_email, user_provider = result.first()
        await self.db.commit()

        payload = {
            "id": id,
            "user_email": user_email,
            "user_provider": user_provider
        }

        # dict -> pydantic
        claim_dto = UserClaimDTO.model_validate(payload)
        return claim_dto

    # 1. 소셜 회원 조회(provider, provider_id)
    async def find_user_by_provider(self, user_provider: str, user_provider_id: str):
        query = (
            select(User)
                .where(
                    User.user_provider == user_provider,
                    User.user_provider_id == user_provider_id
                )
        )

        result = await self.db.execute(query)
        found_user = result.scalar_one_or_none()
        return found_user


    async def find_user_by_email_and_provider(self, user_email:str, user_provider: str):
        query = (
            select(User)
                .where(
                    User.user_email == user_email,
                    User.user_provider == user_provider,
                )
        )

        result = await self.db.execute(query)
        found_user = result.scalar_one_or_none()
        return found_user


    # 2. 회원 조회(id)
    async def find_user_by_id(self, id: int) -> User | None:
        query = select(User).where(User.id == id)
        result = await self.db.execute(query)
        found_user = result.scalar_one_or_none()
        return found_user

    async def exists_user_by_id(self, id: int) -> bool:
        query = (
            select(exists().where(User.id == id))
        )
        result = await self.db.execute(query)
        return result.scalar()


    # 3. 소셜 회원가입 (소셜 로그인 + 추가정보 입력 후에만 호출)
    async def create_user(self, new_user: UserCreateDTO) -> UserClaimDTO:
        # pydantic -> dict (enum은 문자열로 변환)
        values = new_user.model_dump(mode="json")
        query = (
            insert(User)
            .values(**values)
        ).returning(
            User.id,
            User.user_provider
        )

        result = await self.db.execute(query)
        # 필요한 값만 리턴(id, provider)
        id, user_provider = result.first()

        payload = {
            "id": id,
            "user_provider": user_provider
        }

        # dict -> pydantic
        claim_dto = UserClaimDTO.model_validate(payload)

        await self.db.commit()
        return claim_dto


    # 7. 회원 정보 수정
    async def update_user(self, id: int, update_data: dict) -> User | None:
        if not update_data:
            return None

        # 업데이트 시 None 제외
        query = (
            update(User)
            .where(User.id == id)
            .values(**update_data)
            .returning(User)
        )

        result = await self.db.execute(query)
        await self.db.commit()

        updated_user = result.scalar_one_or_none()
        return updated_user


    # 8. 회원 삭제
    async def delete_user(self, id: int):
        query = (
            delete(User)
                .where(User.id == id)
        )

        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

# 주입 팩토리 메서드
def get_user_repository(db: AsyncSession = Depends(get_postgresql_db)):
    return UserRepository(db)
