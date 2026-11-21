from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: posts / 게시글)
class PostVO(BaseModel):
    id: int

    post_category: str
    post_title: str
    post_content: str
    post_status: str
    post_created_at: datetime
    post_updated_at: datetime | None = None
    post_like: int

    user_id: int
