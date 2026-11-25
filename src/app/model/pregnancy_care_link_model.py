from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, String, Boolean, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.pregnancy_model import Pregnancy
    from app.model.doctor_model import Doctor

KST = timezone(timedelta(hours=9))  # UTC+9

class PregnancyCareLink(Base):
    __tablename__ = "pregnancy_care_links"  # 임신·병원·의료진 연결

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    preg_care_link_code: Mapped[str] = mapped_column(String(128), nullable=False)  # 연결 코드
    preg_care_link_code_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 연결 코드 만료 일시
    preg_care_link_approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 산모 승인 일시
    preg_care_link_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # 연결 상태
    preg_care_link_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 연결 해제 일시

    # 관계
    pregnancy_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pregnancies.id"), nullable=False)  # 외래키 (FK)
    doctor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("doctors.id"), nullable=False)  # 외래키 (FK)
    pregnancy: Mapped["Pregnancy"] = relationship("Pregnancy", back_populates="pregnancy_care_links")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="pregnancy_care_links")
