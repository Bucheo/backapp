from pydantic import BaseModel
from app.enum.fetus_enum import FetusGender

# VO (ERD 테이블: fetuses / 태아 정보)
class FetusVO(BaseModel):
    id: int

    fetus_name: str
    fetus_gender: FetusGender

    pregnancy_id: int
