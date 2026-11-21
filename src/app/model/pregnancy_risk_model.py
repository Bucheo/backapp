from sqlalchemy import BigInteger, String, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.prenatal_record_model import PrenatalRecord

class PregnancyRisk(Base):
    __tablename__ = "pregnancy_risks"  # AI 위험도 예측

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    preg_risk_premature_birth_risk: Mapped[str | None] = mapped_column(String(20))  # 조산 위험도
    preg_risk_health_risk: Mapped[str | None] = mapped_column(String(20))  # 산모 건강 위험도

    # 관계
    prenatal_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("prenatal_records.id"), nullable=False)  # 외래키 (FK)
    prenatal_record: Mapped["PrenatalRecord"] = relationship("PrenatalRecord", back_populates="pregnancy_risks")
