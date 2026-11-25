from pydantic import BaseModel
from datetime import datetime
from app.enum.pregnancy_enum import PregnancyStatus

# VO (ERD 테이블: pregnancies / 임신 정보)
class PregnancyVO(BaseModel):
    id: int

    pregnancy_previous_pregnancy: int = 0
    pregnancy_previous_birth: int = 0
    pregnancy_gestational_weeks: int
    pregnancy_gestational_reference: datetime | None = None
    pregnancy_due_date: datetime | None = None
    pregnancy_status: PregnancyStatus
    pregnancy_ended_on: datetime | None = None
    pregnancy_code: str

    user_id: int
