from enum import Enum

class HospitalTypeEnum(str, Enum):
    EMERGENCYROOM = "EMERGENCYROOM" # 응급실
    OBSTETRICS = "OBSTETRICS"       # 산부인과
    