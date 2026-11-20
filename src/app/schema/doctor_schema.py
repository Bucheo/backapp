from pydantic import BaseModel

# VO (ERD 테이블: doctors / 의료진)
class DoctorVO(BaseModel):
    id: int

    doctor_name: str
    doctor_profession: str
    doctor_license_number: str | None = None
    doctor_verification_file_key: str | None = None
    doctor_verification_status: str
    doctor_hospital: str

    user_id: int
