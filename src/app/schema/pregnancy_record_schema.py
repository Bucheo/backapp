from pydantic import BaseModel
from datetime import datetime
from app.enum.pregnancy_enum import PregRecordCondition

# VO (ERD 테이블: pregnancy_records / 산모 증상 일지)
class PregnancyRecordVO(BaseModel):
    id: int

    preg_record_date: datetime
    preg_record_memo: str | None = None
    preg_record_survey_version: str
    preg_record_survey_answers: str
    preg_record_condition: PregRecordCondition

    pregnancy_id: int
