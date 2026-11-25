from sqlalchemy import BigInteger, String, Identity, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.pregnancy_model import Pregnancy

class Fetus(Base):
    __tablename__ = "fetuses"  # 태아 정보

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    fetus_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 태명
    fetus_gender: Mapped[str] = mapped_column(String(20), nullable=False)  # 태아 성별 (MALE, FEMALE, UNKNOWN)

    # 관계
    pregnancy_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pregnancies.id"), nullable=False)  # 외래키 (FK)
    pregnancy: Mapped["Pregnancy"] = relationship("Pregnancy", back_populates="fetuses")
