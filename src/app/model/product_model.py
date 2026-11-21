from sqlalchemy import BigInteger, String, Text, Integer, Boolean, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.order_model import Order

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # 상품명
    product_category: Mapped[str] = mapped_column(String(40), nullable=False)  # 카테고리
    product_description: Mapped[str | None] = mapped_column(Text)  # 상품 설명
    product_image_url: Mapped[str | None] = mapped_column(Text)  # 상품 이미지 주소
    product_seller: Mapped[str] = mapped_column(String(160), nullable=False)  # 판매처
    product_external_url: Mapped[str] = mapped_column(Text, nullable=False)  # 외부 판매 주소
    product_is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False)  # 노출 여부
    product_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 상품 가격

    # 관계
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="product", cascade="all, delete-orphan")
