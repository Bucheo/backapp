from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, String, Text, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.pregnancy_model import Pregnancy

KST = timezone(timedelta(hours=9))  # UTC+9

class PregnancyRecord(Base):
    __tablename__ = "pregnancy_records"  # 임신 증상 일지

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    preg_record_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 기록 날짜
    preg_record_symptom_content: Mapped[str] = mapped_column(Text, nullable=False)  # 증상 내용
    preg_record_survey_version: Mapped[str] = mapped_column(String(40), nullable=False)  # 설문 양식 버전(기록 날짜 기준 최신 버전)
    preg_record_survey_answers: Mapped[str] = mapped_column(Text, nullable=False)  # 설문 응답 데이터

    # 관계
    pregnancy_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pregnancies.id"), nullable=False)  # 외래키 (FK)
    pregnancy: Mapped["Pregnancy"] = relationship("Pregnancy", back_populates="pregnancy_records")
