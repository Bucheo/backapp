from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: reservations / 병원 예약)
class ReservationVO(BaseModel):
    id: int

    reservations_date: datetime
    reservations_about: str

    doctor_id: int | None = None
    pregnancy_id: int | None = None
