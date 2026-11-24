from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import load_only
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.postgresql import get_postgresql_db
from app.model.doctor_model import Doctor


class DoctorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def login_query():
        # 이미지 저장 등 가입 확장 필드는 로그인 단계에서 읽지 않습니다.
        return select(Doctor).options(load_only(
            Doctor.id, Doctor.doctor_provider, Doctor.doctor_provider_id,
            Doctor.doctor_name, Doctor.doctor_phone, Doctor.doctor_profession,
            Doctor.doctor_hospital, Doctor.doctor_status, Doctor.doctor_deleted_at,
            Doctor.doctor_verification_status,
        ))

    async def find_by_provider(self, provider: str, provider_id: str) -> Doctor | None:
        # 이메일이 같아도 일반 회원이나 다른 소셜 계정과 자동 연결하지 않습니다.
        result = await self.db.execute(self.login_query().where(
            Doctor.doctor_provider == provider,
            Doctor.doctor_provider_id == provider_id,
        ))
        return result.scalar_one_or_none()

    async def find_by_id(self, doctor_id: int) -> Doctor | None:
        result = await self.db.execute(self.login_query().where(Doctor.id == doctor_id))
        return result.scalar_one_or_none()


def get_doctor_repository(db: AsyncSession = Depends(get_postgresql_db)):
    return DoctorRepository(db)
