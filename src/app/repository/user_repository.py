from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.postgresql import get_postgresql_db
from fastapi import Depends

# 모델, ORM
from app.model.user_model import User
from app.model.agree_model import Agree
from app.schema.user_schema import UserCreateDTO, UserClaimDTO
from sqlalchemy import insert, select, update, delete, func, exists  # CRUD 순서


class UserRepository:

    # 생성자 주입
    def __init__(self, db: AsyncSession):
        self.db = db


    # 순수 함수
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
    # agree_values가 있으면 users와 agrees를 하나의 트랜잭션으로 저장한다
    # (둘 중 하나라도 실패하면 전체 롤백)
    async def create_user(
        self, new_user: UserCreateDTO, agree_values: dict | None = None
    ) -> UserClaimDTO:
        # pydantic -> dict (enum은 문자열로 변환)
        values = new_user.model_dump(mode="json")
        query = (
            insert(User)
            .values(**values)
        ).returning(
            User.id,
            User.user_provider
        )

        try:
            result = await self.db.execute(query)
            # 필요한 값만 리턴(id, provider)
            id, user_provider = result.first()

            # 약관 동의 저장 (agrees.user_id = 방금 생성된 users.id)
            if agree_values is not None:
                await self.db.execute(
                    insert(Agree).values(user_id=id, **agree_values)
                )

            # users + agrees를 한 번에 커밋
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        payload = {
            "id": id,
            "user_provider": user_provider
        }

        # dict -> pydantic
        return UserClaimDTO.model_validate(payload)


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
