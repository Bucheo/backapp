from sqlalchemy import BigInteger, Text, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.pregnancy_record_model import PregnancyRecord

class PregnancySymptom(Base):
    __tablename__ = "pregnancy_symptoms"  # 산모 증상 종류

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    preg_symptoms_type: Mapped[str] = mapped_column(Text, nullable=False)  # 증상 종류 (입덧, 두통, 복통, ... 기타)

    # 관계
    pregnancy_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pregnancy_records.id"), nullable=False)  # 외래키 (FK)
    pregnancy_record: Mapped["PregnancyRecord"] = relationship("PregnancyRecord", back_populates="pregnancy_symptoms")
