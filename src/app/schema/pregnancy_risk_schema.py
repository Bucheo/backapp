from pydantic import BaseModel

# VO (ERD 테이블: pregnancy_risks / 조기 위험도 예측)
class PregnancyRiskVO(BaseModel):
    id: int

    pregnancy_risks_premature_birth_risk: str | None = None
    pregnancy_risks_health_risk: str | None = None

    prenatal_record_id: int
