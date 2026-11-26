from enum import Enum

class PregnancyStatus(str, Enum):
    BIRTH = "BIRTH"                     # 출산 완료
    PREBIRTH = "PREBIRTH"               # 임신 중

class PregEndRequestOutcome(str, Enum):
    PREMATUREBIRTH = "PREMATUREBIRTH"   # 조산
    ABORTION = "ABORTION"               # 유산
    FULLTERM = "FULLTERM"               # 만삭

class PregEndRequestStatus(str, Enum):
    ACCEPT = "ACCEPT"                   # 수리
    REJECT = "REJECT"                   # 반려
    CONSIDERING = "CONSIDERING"         # 검토중

# 산모 증상 일지 - 컨디션 (ERD 값 그대로)
class PregRecordCondition(str, Enum):
    VERY_GOOD = "VERY_GOOD"
    GOOD = "GOOD"
    NORMAL = "NORMAL"
    BAD = "BAD"
    VERY_BAD = "VERY_BAD"

# 산모 증상 종류 (ERD 값 그대로)
class PregSymptomType(str, Enum):
    MORNING_SICKNESS = "MORNING_SICKNESS"               # 입덧
    HEADACHE = "HEADACHE"                               # 두통
    ABDOMINAL_PAIN = "ABDOMINAL_PAIN"                   # 복통
    BACK_PAIN = "BACK_PAIN"                             # 허리 통증
    EDEMA = "EDEMA"                                     # 부종
    FATIGUE = "FATIGUE"                                 # 피로감
    DIZZINESS = "DIZZINESS"                             # 어지러움
    HEARTBURN = "HEARTBURN"                             # 속쓰림
    FETAL_MOVEMENT_CHANGE = "FETAL_MOVEMENT_CHANGE"     # 태동 변화
    SLEEP_PROBLEM = "SLEEP_PROBLEM"                     # 수면 문제
    ETC = "ETC"                                         # 기타
