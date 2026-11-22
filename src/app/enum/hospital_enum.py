from enum import Enum


class HospitalTypeEnum(str, Enum):
    # 원본 분만 가능 의료기관 CSV의 '종별' 값을 그대로 사용합니다.
    TERTIARY_GENERAL_HOSPITAL = "상급종합병원"
    GENERAL_HOSPITAL = "종합병원"
    HOSPITAL = "병원"
    CLINIC = "의원"
    MIDWIFERY_CENTER = "조산원"
