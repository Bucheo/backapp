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
