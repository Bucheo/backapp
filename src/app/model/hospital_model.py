from sqlalchemy import BigInteger, Text, Integer, Boolean, Identity, Numeric
from sqlalchemy.orm import Mapped, mapped_column

# PostgreSQL의 Base를 상속받아서 서버가 켜질 때 동기화시킨다.
from app.infrastructure.postgresql import Base

class Hospital(Base):
    __tablename__ = "hospitals"  # 병원

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # 기본키 (PK)
    hospital_latitude: Mapped[float] = mapped_column(Numeric, nullable=False)  # 위도
    hospital_longitude: Mapped[float] = mapped_column(Numeric, nullable=False)  # 경도
    hospital_type: Mapped[str] = mapped_column(Text, nullable=False)  # 종별 (응급실, 산부인과 전문)
    hospital_name: Mapped[str] = mapped_column(Text, nullable=False)  # 기관명
    hospital_address: Mapped[str] = mapped_column(Text, nullable=False)  # 주소
    hospital_phone: Mapped[str] = mapped_column(Text, nullable=False)  # 전화번호
    hospital_night_service: Mapped[bool] = mapped_column(Boolean, nullable=False)  # 야간 운영 여부
