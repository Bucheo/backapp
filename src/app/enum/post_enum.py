from enum import Enum

# 게시 상태 (ERD: 게시중, 게시 완료, 게시 불가)
class PostStatus(str, Enum):
    POSTING = "POSTING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"

# 작성자 타입 (ERD: 보호자, 예비맘, 육아맘)
class PostWriterType(str, Enum):
    GUARDIAN = "GUARDIAN"
    EXPECTANT_MOM = "EXPECTANT_MOM"
    PARENTING_MOM = "PARENTING_MOM"

class 