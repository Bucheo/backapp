from pydantic import BaseModel
from datetime import datetime
from app.enum.pregnancy_enum import PregEndRequestOutcome, PregEndRequestStatus

# VO (ERD 테이블: pregnancy_end_requests / 임신 종료 신청)
class PregnancyEndRequestVO(BaseModel):
    id: int

    preg_end_request_outcome: PregEndRequestOutcome
    preg_end_request_ended_on: datetime
    preg_end_request_status: PregEndRequestStatus
    preg_end_request_confirmed_at: datetime | None = None

    fetus_id: int
    doctor_id: int
