from enum import Enum

class S3Folder(str, Enum):
    # 게시판, 프로필
    POST = "post"
    PROFILE = "profile"