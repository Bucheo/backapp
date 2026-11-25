from datetime import datetime
from sqlalchemy import BigInteger, Text, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.doctor_model import Doctor
    from app.model.pregnancy_model import Pregnancy

class Reservation(Base):
    __tablename__ = "reservations"  # 병원 예약

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    reservations_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 예약 일시
    reservations_about: Mapped[str] = mapped_column(Text, nullable=False)  # 검사 종류

    # 관계
    doctor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("doctors.id"), nullable=True)  # 외래키 (FK)
    pregnancy_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("pregnancies.id"), nullable=True)  # 외래키 (FK)
    doctor: Mapped["Doctor | None"] = relationship("Doctor", back_populates="reservations")
    pregnancy: Mapped["Pregnancy | None"] = relationship("Pregnancy", back_populates="reservations")
