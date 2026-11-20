from pydantic import BaseModel
from datetime import datetime

# VO (ERD 테이블: orders / 주문)
class OrderVO(BaseModel):
    id: int

    order_quantity: int
    order_status: str
    order_created_at: datetime
    order_shipped_at: datetime | None = None
    order_delivered_at: datetime | None = None
    order_cancelled_at: datetime | None = None

    product_id: int
    user_id: int
