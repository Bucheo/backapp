from enum import Enum

class OrderStatusEnum(str, Enum):
    ONDELIVERY = "ONDELIVERY"  # 배송중
    COMPLETE = "COMPLETE"      # 배송 완료
    UNSHIPPED = "UNSHIPPED"    # 출고 안 됨