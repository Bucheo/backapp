from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: relationship / 임신-보호자 연결)
class RelationshipVO(BaseModel):
    id: int

    relationship_status: bool
    relationship_access_scope: str
    relationship_approved_at: datetime | None = None
    relationship_revoked_at: datetime | None = None

    pregnancy_id: int
    user_id: int
