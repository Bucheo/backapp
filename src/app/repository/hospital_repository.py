from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enum.hospital_enum import HospitalTypeEnum
from app.infrastructure.postgresql import get_postgresql_db
from app.model.hospital_model import Hospital


class HospitalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_hospitals(self, hospital_type: HospitalTypeEnum | None = None) -> list[Hospital]:
        # 현재 규모에서는 목록 전체를 전달하고 지도 범위 필터는 프론트에서 처리합니다.
        statement = select(Hospital).order_by(Hospital.id)
        if hospital_type is not None:
            statement = statement.where(Hospital.hospital_type == hospital_type)

        result = await self.db.execute(statement)
        return list(result.scalars().all())


def get_hospital_repository(db: AsyncSession = Depends(get_postgresql_db)):
    return HospitalRepository(db)
