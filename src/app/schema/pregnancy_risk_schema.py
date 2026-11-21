from pydantic import BaseModel

# VO (ERD 테이블: pregnancy_risks / 조기 위험도 예측)
class PregnancyRiskVO(BaseModel):
    id: int

    preg_risk_premature_birth_risk: str | None = None
    preg_risk_health_risk: str | None = None

    prenatal_record_id: int
