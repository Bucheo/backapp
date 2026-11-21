from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: comments / 댓글)
class CommentVO(BaseModel):
    id: int

    comment_content: str
    comment_is_secret: bool
    comment_created_at: datetime
    comment_updated_at: datetime | None = None

    post_id: int
    user_id: int
