from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: pregnancy_end_requests / 임신 종료 신청)
class PregnancyEndRequestVO(BaseModel):
    id: int

    per_outcome: str
    per_ended_on: datetime
    per_status: str
    per_confirmed_at: datetime | None = None

    pregnancy_id: int
    doctor_id: int
