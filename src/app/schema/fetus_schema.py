from pydantic import BaseModel, Field
from app.enum.fetus_enum import FetusGender

# VO (ERD 테이블: fetuses / 태아 정보)
class FetusVO(BaseModel):
    id: int

    fetus_name: str
    fetus_gender: FetusGender

    pregnancy_id: int

class FetusCreateDTO(BaseModel):
    fetus_name: str = Field(min_length=1, max_length=100)  # 태명 (1~100자)
    fetus_gender: FetusGender