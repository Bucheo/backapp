from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.pregnancy_model import Pregnancy
    from app.model.doctor_model import Doctor

class PregnancyEndRequest(Base):
    __tablename__ = "pregnancy_end_requests"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    per_outcome: Mapped[str] = mapped_column(String(40), nullable=False)  # 종료 종류 (조산, 유산, 만삭)
    per_ended_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 종료 날짜
    per_status: Mapped[str] = mapped_column(String(40), nullable=False)  # 신청 상태 (수락, 반려, 검토중)
    per_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 종료 확정 일시

    # 관계
    pregnancy_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pregnancies.id"), nullable=False)  # 외래키 (FK)
    doctor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("doctors.id"), nullable=False)  # 외래키 (FK)
    pregnancy: Mapped["Pregnancy"] = relationship("Pregnancy", back_populates="pregnancy_end_requests")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="pregnancy_end_requests")
