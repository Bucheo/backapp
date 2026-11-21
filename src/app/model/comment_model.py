from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, String, Text, Boolean, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.post_model import Post
    from app.model.user_model import User

KST = timezone(timedelta(hours=9))  # UTC+9

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    comment_content: Mapped[str] = mapped_column(Text, nullable=False)  # 댓글 내용
    comment_is_secret: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 비밀댓글 여부
    comment_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 작성 일시
    comment_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 수정 일시

    # 관계
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id"), nullable=False)  # 외래키 (FK)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)  # 외래키 (FK)
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
