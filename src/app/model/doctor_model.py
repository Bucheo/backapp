from sqlalchemy import BigInteger, String, Text, Boolean, Identity, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta, timezone

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.user_model import User
    from app.model.pregnancy_care_link_model import PregnancyCareLink
    from app.model.prenatal_record_model import PrenatalRecord
    from app.model.pregnancy_end_request_model import PregnancyEndRequest

class Doctor(Base):
    __tablename__ = "doctors"  # 의료진

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    doctor_name: Mapped[str] = mapped_column(String(40), nullable=False)  # 실명
    doctor_phone: Mapped[str] = mapped_column(String(20), nullable=False)  # 전화번호
    doctor_profession: Mapped[str] = mapped_column(String(40), nullable=False)  # 의료진 직종(분야)
    doctor_license_number: Mapped[str | None] = mapped_column(String(100))  # 면허번호
    doctor_verification_file_key: Mapped[str | None] = mapped_column(Text)  # 증빙 파일 식별자
    doctor_verification_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 자격 검증 상태
    doctor_hospital: Mapped[str] = mapped_column(Text, nullable=False)  # 소속 병원명
    doctor_provider: Mapped[str] = mapped_column(String(40), nullable=False)  # 소셜 로그인 제공자 (GOOGLE, NAVER, KAKAO)
    doctor_provider_id: Mapped[str] = mapped_column(String(255), nullable=False)  # 제공자 회원 ID
    doctor_email: Mapped[str] = mapped_column(String(255), nullable=False)  # 이메일
    doctor_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # 계정 상태 (True, False)
    doctor_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 가입 일시
    doctor_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 탈퇴 일시

    # 관계
    pregnancy_care_links: Mapped[list["PregnancyCareLink"]] = relationship("PregnancyCareLink", back_populates="doctor", cascade="all, delete-orphan")
    prenatal_records: Mapped[list["PrenatalRecord"]] = relationship("PrenatalRecord", back_populates="doctor", cascade="all, delete-orphan")
    pregnancy_end_requests: Mapped[list["PregnancyEndRequest"]] = relationship("PregnancyEndRequest", back_populates="doctor", cascade="all, delete-orphan")
