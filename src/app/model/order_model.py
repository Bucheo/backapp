from datetime import datetime, timedelta, timezone
from sqlalchemy import BigInteger, Integer, String, DateTime, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.product_model import Product
    from app.model.user_model import User

KST = timezone(timedelta(hours=9))  # UTC+9

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    order_quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # 주문수량
    order_status: Mapped[str] = mapped_column(String(30), nullable=False)  # 배송 상태 (배달중, 출고 안됨, 배달 완료)
    order_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(KST))  # 주문 일시
    order_shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 배송 시작 일시
    order_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 배송 완료 일시
    order_cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 취소 일시

    # 관계
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"), nullable=False)  # 외래키 (FK)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)  # 외래키 (FK)
    product: Mapped["Product"] = relationship("Product", back_populates="orders")
    user: Mapped["User"] = relationship("User", back_populates="orders")
