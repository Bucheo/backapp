from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, Text, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.fetus_model import Fetus
    from app.model.doctor_model import Doctor
    from app.model.pregnancy_risk_model import PregnancyRisk

KST = timezone(timedelta(hours=9))  # UTC+9

class PrenatalRecord(Base):
    __tablename__ = "prenatal_records"  # 병원 검진 기록

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    pren_record_visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 검진 일시
    pren_record_confirmed_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 병원 확인 출산 예정일
    pren_record_examination_notes: Mapped[str | None] = mapped_column(Text)  # 검진 내용
    pren_record_ehg: Mapped[str | None] = mapped_column(Text)  # EHG 수치 (ERD 타입 미정 - 추후 따로 ehg 타입 생성 예정)
    pren_record_test_results: Mapped[str | None] = mapped_column(Text)  # 검사 결과
    pren_record_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 작성 일시

    # 관계
    fetus_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("fetuses.id"), nullable=False)  # 외래키 (FK)
    doctor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("doctors.id"), nullable=False)  # 외래키 (FK)
    fetus: Mapped["Fetus"] = relationship("Fetus", back_populates="prenatal_records")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="prenatal_records")
    pregnancy_risks: Mapped[list["PregnancyRisk"]] = relationship("PregnancyRisk", back_populates="prenatal_record", cascade="all, delete-orphan")
