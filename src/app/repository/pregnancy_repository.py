from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.postgresql import get_postgresql_db
from fastapi import Depends

# 모델, ORM
from app.model.pregnancy_model import Pregnancy
from app.model.fetus_model import Fetus
from sqlalchemy import insert, select, func, exists  # CRUD 순서


class PregnancyRepository:

    # 생성자 주입
    def __init__(self, db: AsyncSession):
        self.db = db


    # 순수 함수
    # 1. 보호자 승인 코드 중복 확인
    async def exists_pregnancy_by_code(self, pregnancy_code: str) -> bool:
        query = select(exists().where(Pregnancy.pregnancy_code == pregnancy_code))
        result = await self.db.execute(query)
        return result.scalar()


    # 2. 사용자의 진행 중인 임신 개수 조회 (상태가 PREBIRTH인 임신)
    async def count_pregnancies_by_user_and_status(self, user_id: int, pregnancy_status: str) -> int:
        query = (
            select(func.count())
            .select_from(Pregnancy)
            .where(
                Pregnancy.user_id == user_id,
                Pregnancy.pregnancy_status == pregnancy_status,
            )
        )
        result = await self.db.execute(query)
        return result.scalar()


    # 3. 임신 + 태아 저장
    # pregnancies를 먼저 저장해서 id를 받고, 그 id를 태아(fetuses)의 pregnancy_id에 넣는다.
    # 둘 중 하나라도 실패하면 전체 롤백 (하나의 트랜잭션)
    #   pregnancy_values: 임신 테이블에 넣을 값 dict (user_id, pregnancy_code 등 포함)
    #   fetus_values_list: 태아별 값 dict 리스트 (fetus_name, fetus_gender)
    async def create_pregnancy_with_fetuses(
        self, pregnancy_values: dict, fetus_values_list: list[dict]
    ) -> int:
        pregnancy_query = (
            insert(Pregnancy)
            .values(**pregnancy_values)
            .returning(Pregnancy.id)
        )

        try:
            result = await self.db.execute(pregnancy_query)
            pregnancy_id = result.scalar_one()

            # 태아 여러 명(쌍둥이 등)을 한 번에 저장
            if fetus_values_list:
                await self.db.execute(
                    insert(Fetus),
                    [{**fetus_values, "pregnancy_id": pregnancy_id} for fetus_values in fetus_values_list],
                )

            # pregnancies + fetuses를 한 번에 커밋
            await self.db.commit()
        except Exception:
            await self.db.rollback("self.create_pregnancy_with_fetuses 오류")
            raise

        return pregnancy_id


# 주입 팩토리 메서드
def get_pregnancy_repository(db: AsyncSession = Depends(get_postgresql_db)):
    return PregnancyRepository(db)
