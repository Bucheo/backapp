from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, String, DateTime, Identity, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.agree_model import Agree
    from app.model.post_model import Post
    from app.model.comment_model import Comment
    from app.model.pregnancy_model import Pregnancy
    from app.model.relationship_model import Relationship
    from app.model.doctor_model import Doctor
    from app.model.order_model import Order

KST = timezone(timedelta(hours=9))  # UTC+9

class User(Base):
    __tablename__ = "users"  # 회원

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    user_name: Mapped[str] = mapped_column(String(40), nullable=False)  # 실명
    user_provider: Mapped[str] = mapped_column(String(40), nullable=False)  # 소셜 로그인 제공자 (GOOGLE, NAVER, KAKAO)
    user_provider_id: Mapped[str] = mapped_column(String(255), nullable=False)  # 제공자 회원 ID
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)  # 이메일
    user_nickname: Mapped[str] = mapped_column(String(40), nullable=False)  # 닉네임
    user_phone: Mapped[str] = mapped_column(String(20), nullable=False)  # 전화번호
    user_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # 계정 상태 (True, False)
    user_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 가입 일시
    user_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 탈퇴 일시

    # 관계
    # cascade: User가 삭제되면 참조된 테이블을 모두 같이 연쇄삭제
    agree: Mapped["Agree | None"] = relationship("Agree", back_populates="user", uselist=False, cascade="all, delete-orphan")
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    pregnancies: Mapped[list["Pregnancy"]] = relationship("Pregnancy", back_populates="user", cascade="all, delete-orphan")
    relationships: Mapped[list["Relationship"]] = relationship("Relationship", back_populates="user", cascade="all, delete-orphan")
    doctors: Mapped[list["Doctor"]] = relationship("Doctor", back_populates="user", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")
