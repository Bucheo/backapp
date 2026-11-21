from enum import Enum

class PregnancyStatus(str, Enum):  # enum으로 각 provider에 해당하는 타입을 새로 만듦
    # LOCAL = "LOCAL"
    BIRTH = "BIRTH"
    BIRTH = "PREBIRTH"

class PerOutcome(str, Enum):  # enum으로 각 provider에 해당하는 타입을 새로 만듦
    # LOCAL = "LOCAL"
    BIRTH = "BIRTH"
    BIRTH = "PREBIRTH"