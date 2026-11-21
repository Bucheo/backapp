from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, Integer, SmallInteger, String, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.user_model import User
    from app.model.relationship_model import Relationship
    from app.model.pregnancy_care_link_model import PregnancyCareLink
    from app.model.prenatal_record_model import PrenatalRecord
    from app.model.pregnancy_end_request_model import PregnancyEndRequest
    from app.model.pregnancy_record_model import PregnancyRecord

KST = timezone(timedelta(hours=9))  # UTC+9

class Pregnancy(Base):
    __tablename__ = "pregnancies"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    pregnancy_baby_nickname: Mapped[str] = mapped_column(String(100), nullable=False)  # 태명
    pregnancy_previous_pregnancy: Mapped[int | None] = mapped_column(Integer)  # 이전 임신 횟수
    pregnancy_previous_birth: Mapped[int | None] = mapped_column(Integer)  # 이전 출산 횟수
    pregnancy_gestational_weeks: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 등록 당시 임신 주수
    pregnancy_gestational_reference: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 임신 주수 기준일
    pregnancy_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 출산 예정일
    pregnancy_status: Mapped[str] = mapped_column(String(40), nullable=False)  # 임신 상태 (BIRTH, PREBIRTH)
    pregnancy_ended_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 종료일
    pregnancy_code: Mapped[str] = mapped_column(String(20), nullable=False)  # 보호자 승인 코드

    # 관계
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)  # 외래키 (FK)
    user: Mapped["User"] = relationship("User", back_populates="pregnancies")
    relationships: Mapped[list["Relationship"]] = relationship("Relationship", back_populates="pregnancy", cascade="all, delete-orphan")
    pregnancy_care_links: Mapped[list["PregnancyCareLink"]] = relationship("PregnancyCareLink", back_populates="pregnancy", cascade="all, delete-orphan")
    prenatal_records: Mapped[list["PrenatalRecord"]] = relationship("PrenatalRecord", back_populates="pregnancy", cascade="all, delete-orphan")
    pregnancy_end_requests: Mapped[list["PregnancyEndRequest"]] = relationship("PregnancyEndRequest", back_populates="pregnancy", cascade="all, delete-orphan")
    pregnancy_records: Mapped[list["PregnancyRecord"]] = relationship("PregnancyRecord", back_populates="pregnancy", cascade="all, delete-orphan")
