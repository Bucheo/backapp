from pydantic import BaseModel

# VO (ERD 테이블: hospitals / 병원)
class HospitalVO(BaseModel):
    id: int

    hospital_latitude: int
    hospital_longitude: int
    hospital_registration_file_key: str
    hospital_address: str
    hospital_phone: str
    hospital_opening_hours: str
    hospital_night_service: bool
