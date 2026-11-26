from pydantic import BaseModel
from app.enum.pregnancy_enum import PregSymptomType

# VO (ERD 테이블: pregnancy_symptoms / 산모 증상 종류)
class PregnancySymptomVO(BaseModel):
    id: int

    preg_symptoms_type: PregSymptomType

    pregnancy_record_id: int
