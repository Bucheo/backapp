from sqlalchemy import BigInteger, String, Integer, Identity, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
# 기존 posts 테이블은 create_all 로 컬럼이 추가되지 않으므로, 게시글 부가 정보는 새 테이블로 분리한다.
from app.infrastructure.postgresql import Base


class PostExtra(Base):
    __tablename__ = "post_extras"  # 게시글 부가 정보 (말머리, 동영상, 장소, 투표)

    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)  # PK 겸 FK
    post_prefix: Mapped[str] = mapped_column(String(40), nullable=False, default="질문")  # 말머리
    video_key: Mapped[str | None] = mapped_column(String(500))  # 동영상 S3 key
    video_url: Mapped[str | None] = mapped_column(String(1000))  # 동영상 URL
    video_duration: Mapped[int | None] = mapped_column(Integer)  # 동영상 길이(초)
    place_name: Mapped[str | None] = mapped_column(String(200))  # 장소 이름
    place_address: Mapped[str | None] = mapped_column(String(300))  # 장소 주소
    poll_question: Mapped[str | None] = mapped_column(String(300))  # 투표 질문
    poll_options: Mapped[list | None] = mapped_column(JSON)  # 투표 항목 ["항목1", "항목2", ...]


class PostPhoto(Base):
    __tablename__ = "post_photos"  # 게시글 사진

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_key: Mapped[str] = mapped_column(String(500), nullable=False)  # 원본 S3 key
    photo_url: Mapped[str] = mapped_column(String(1000), nullable=False)  # 원본 URL
    thumb_url: Mapped[str | None] = mapped_column(String(1000))  # 썸네일 URL
    photo_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 표시 순서


class PostPollVote(Base):
    __tablename__ = "post_poll_votes"  # 투표 참여 (회원당 게시글 1회)
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_poll_vote"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    option_index: Mapped[int] = mapped_column(Integer, nullable=False)
