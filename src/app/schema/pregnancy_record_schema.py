from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: pregnancy_records / 산모 증상 일지)
class PregnancyRecordVO(BaseModel):
    id: int

    preg_record_date: datetime
    preg_record_symptom_content: str | None = None
    preg_record_survey_version: str | None = None
    preg_record_survey_answers: str | None = None

    user_id: int
