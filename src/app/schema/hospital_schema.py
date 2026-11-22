from pydantic import BaseModel
from app.enum.hospital_enum import HospitalTypeEnum

# VO (ERD 테이블: hospitals / 병원)
class HospitalVO(BaseModel):
    id: int

    hospital_latitude: float
    hospital_longitude: float
    hospital_type: HospitalTypeEnum
    hospital_name: str
    hospital_address: str
    hospital_phone: str
    hospital_night_service: bool
