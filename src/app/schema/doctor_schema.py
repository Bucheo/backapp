from pydantic import BaseModel
from app.enum.user_enum import UserProvider
from datetime import datetime

# VO (ERD 테이블: doctors / 의료진)
class DoctorVO(BaseModel):
    id: int

    doctor_name: str
    doctor_phone: str
    doctor_profession: str
    doctor_license_number: str | None = None
    doctor_verification_file_key: str | None = None
    doctor_verification_status: bool
    doctor_hospital: str
    doctor_provider: UserProvider
    doctor_provider_id: str
    doctor_email: str
    doctor_status: bool
    doctor_created_at: datetime
    doctor_deleted_at: datetime | None = None

