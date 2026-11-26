from pydantic import BaseModel
from datetime import datetime
from app.enum.calender_enum import CalenderType

# VO (ERD 테이블: calenders / 캘린더)
class CalenderVO(BaseModel):
    id: int

    calender_date: datetime
    calender_memo: str | None = None
    calender_type: CalenderType
    calender_place: str | None = None
    calender_push: bool = False

    pregnancy_id: int
