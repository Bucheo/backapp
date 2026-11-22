from fastapi import Depends

from app.enum.hospital_enum import HospitalTypeEnum
from app.repository.hospital_repository import HospitalRepository, get_hospital_repository
from app.schema.hospital_schema import HospitalVO


class HospitalService:
    def __init__(self, repo: HospitalRepository):
        self.repo = repo

    async def get_hospitals(self, hospital_type: HospitalTypeEnum | None = None) -> list[HospitalVO]:
        hospitals = await self.repo.get_hospitals(hospital_type)
        # ORM 객체를 VO로 변환해 좌표(float)와 기관 유형(Enum)을 함께 검사합니다.
        return [HospitalVO.model_validate(hospital, from_attributes=True) for hospital in hospitals]


def get_hospital_service(repo: HospitalRepository = Depends(get_hospital_repository)):
    return HospitalService(repo)
