from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: prenatal_records / 병원 검진 기록)
class PrenatalRecordVO(BaseModel):
    id: int

    pren_record_visited_at: datetime
    pren_record_confirmed_due_date: datetime | None = None
    pren_record_examination_notes: str | None = None
    pren_record_ehg: str | None = None
    pren_record_test_results: str | None = None
    pren_record_created_at: datetime

    pregnancy_id: int
    doctor_id: int
