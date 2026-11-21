from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: pregnancy_care_links / 임신-병원-의료진 연결)
class PregnancyCareLinkVO(BaseModel):
    id: int

    preg_care_link_code: str | None = None
    preg_care_link_code_expires_at: datetime
    preg_care_link_approved_at: datetime
    preg_care_link_status: bool
    preg_care_link_revoked_at: datetime | None = None

    pregnancy_id: int
    doctor_id: int
