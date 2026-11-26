from enum import Enum

# 캘린더 일정 종류 (ERD: 진료, 검사, 초음파)
class CalenderType(str, Enum):
    CHECKUP = "CHECKUP"         # 진료
    TEST = "TEST"               # 검사
    ULTRASOUND = "ULTRASOUND"   # 초음파
