from datetime import datetime
from sqlalchemy import BigInteger, Text, Boolean, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.pregnancy_model import Pregnancy

class Calender(Base):
    __tablename__ = "calenders"  # 캘린더

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    calender_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 날짜
    calender_memo: Mapped[str | None] = mapped_column(Text)  # 메모
    calender_type: Mapped[str] = mapped_column(Text, nullable=False)  # 일정 종류 (진료, 검사, 초음파)
    calender_place: Mapped[str | None] = mapped_column(Text)  # 일정 장소
    calender_push: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 알림 받기 여부

    # 관계
    pregnancy_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pregnancies.id"), nullable=False)  # 외래키 (FK)
    pregnancy: Mapped["Pregnancy"] = relationship("Pregnancy", back_populates="calenders")
