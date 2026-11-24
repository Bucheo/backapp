from typing import Literal
from pydantic import BaseModel

DoctorProviderName = Literal["google", "kakao", "naver"]


class DoctorSocialIdentityDTO(BaseModel):
    doctor_provider: str
    doctor_provider_id: str
    doctor_email: str | None = None


class DoctorSessionDTO(BaseModel):
    id: int
    doctor_name: str
    doctor_phone: str
    doctor_profession: str
    doctor_hospital: str
    doctor_verification_status: bool
    verification_status: Literal["APPROVED", "PENDING"]
