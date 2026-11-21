from enum import Enum

class UserProvider(str, Enum):  # enum으로 각 provider에 해당하는 타입을 새로 만듦
    # LOCAL = "LOCAL"
    GOOGLE = "GOOGLE"
    KAKAO = "KAKAO"
    NAVER = "NAVER"


class UserType(str, Enum):
    GENERAL = "GENENRAL"    # 일반 사용자
    DOCTOR = "DOCTOR"       # 의료진 사용자
