from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, String, Boolean, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.pregnancy_model import Pregnancy
    from app.model.user_model import User

KST = timezone(timedelta(hours=9))  # UTC+9

class Relationship(Base):
    __tablename__ = "relationship"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    relationship_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 승인 상태
    relationship_access_scope: Mapped[str] = mapped_column(String(120), nullable=False)  # 기록 열람 범위
    relationship_approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 승인 일시
    relationship_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 관계 해제 일시

    # 관계
    pregnancy_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pregnancies.id"), nullable=False)  # 외래키 (FK)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)  # 외래키 (FK)
    pregnancy: Mapped["Pregnancy"] = relationship("Pregnancy", back_populates="relationships")
    user: Mapped["User"] = relationship("User", back_populates="relationships")
