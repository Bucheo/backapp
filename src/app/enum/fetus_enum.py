from enum import Enum

class FetusGender(str, Enum):
    MALE = "MALE"               # 남아
    FEMALE = "FEMALE"           # 여아
    UNKNOWN = "UNKNOWN"         # 확인되지 않음
