from pydantic import BaseModel

# VO (ERD 테이블: products / 상품)
class ProductVO(BaseModel):
    id: int

    name: str
    product_category: str
    product_description: str | None = None
    product_image_url: str | None = None
    product_seller: str
    product_external_url: str
    product_is_visible: bool
    product_price: int
