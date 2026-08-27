from app.models import Product
from app.schemas import ProductOut


def to_product_out(product: Product) -> ProductOut:
    """Requires product.stock_item to already be loaded (selectinload) —
    this does not touch the DB itself."""
    stock_remaining = None
    if product.stock_item_id is not None and product.stock_item is not None:
        stock_remaining = product.stock_item.quantity_on_hand // product.portions_per_sale
    return ProductOut(
        product_id=product.product_id,
        name=product.name,
        category=product.category,
        price=float(product.price),
        active=product.active,
        stock_item_id=product.stock_item_id,
        portions_per_sale=product.portions_per_sale,
        stock_remaining=stock_remaining,
    )
