from enum import Enum

class S3Folder(str, Enum):
    # 게시판, 프로필
    COMMUNITY = "COMMUNITY"
    PROFILE = "PROFILE"