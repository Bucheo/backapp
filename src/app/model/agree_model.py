from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.user_model import User

KST = timezone(timedelta(hours=9))  # UTC+9

class Agree(Base):
    __tablename__ = "agrees"

    agree_terms_agreed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 서비스 약관 동의 일시
    agree_terms_version: Mapped[str] = mapped_column(String(40), nullable=False)  # 서비스 약관 버전
    agree_health_data_agreed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 건강정보 처리 동의 일시
    agree_health_data_version: Mapped[str] = mapped_column(String(40), nullable=False)  # 건강정보 동의 버전

    # 관계
    # PK이면서 users를 참조하는 FK (1:1)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)  # 기본키 (PK) · 외래키 (FK)
    user: Mapped["User"] = relationship("User", back_populates="agree")
