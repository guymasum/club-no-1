import io
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_waiter
from app.models import Bill, Order, OrderItem
from app.schemas import BillOut, OrderItemOut

router = APIRouter(tags=["bills"], dependencies=[Depends(get_current_waiter)])

RECEIPT_WIDTH = 80 * mm


async def _load_order_for_bill(order_id: int, db: AsyncSession) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.order_id == order_id)
        .options(
            selectinload(Order.waiter),
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .execution_options(populate_existing=True)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


def _bill_to_out(bill: Bill, order: Order) -> BillOut:
    return BillOut(
        bill_id=bill.bill_id,
        order_id=order.order_id,
        transaction_id=bill.transaction_id,
        total=float(bill.total),
        generated_at=bill.generated_at,
        waiter_name=order.waiter.name,
        customer_name=order.customer.name if order.customer else None,
        items=[
            OrderItemOut(
                item_id=item.item_id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
            )
            for item in order.items
        ],
    )


@router.post("/orders/{order_id}/bill", response_model=BillOut, status_code=status.HTTP_201_CREATED)
async def finalize_order(order_id: int, db: AsyncSession = Depends(get_db)) -> BillOut:
    order = await _load_order_for_bill(order_id, db)

    if order.status == "billed":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Order already billed")
    if not order.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot bill an order with no items")

    total = sum(item.quantity * float(item.unit_price) for item in order.items)
    transaction_id = f"TXN-{datetime.now(UTC):%Y%m%d}-{order.order_id:04d}"

    bill = Bill(order_id=order.order_id, transaction_id=transaction_id, total=total)
    order.status = "billed"
    db.add(bill)
    await db.commit()
    await db.refresh(bill)

    return _bill_to_out(bill, order)


@router.get("/bills/{bill_id}", response_model=BillOut)
async def get_bill(bill_id: int, db: AsyncSession = Depends(get_db)) -> BillOut:
    bill = await db.get(Bill, bill_id)
    if bill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bill not found")
    order = await _load_order_for_bill(bill.order_id, db)
    return _bill_to_out(bill, order)


@router.get("/bills/{bill_id}/pdf")
async def get_bill_pdf(bill_id: int, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    bill = await db.get(Bill, bill_id)
    if bill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bill not found")
    order = await _load_order_for_bill(bill.order_id, db)

    buffer = io.BytesIO()
    height = (120 + 6 * len(order.items)) * mm
    pdf = canvas.Canvas(buffer, pagesize=(RECEIPT_WIDTH, height))
    y = height - 10 * mm
    line = 6 * mm

    def write(text: str, size: int = 9, center: bool = False) -> None:
        nonlocal y
        pdf.setFont("Courier", size)
        if center:
            pdf.drawCentredString(RECEIPT_WIDTH / 2, y, text)
        else:
            pdf.drawString(4 * mm, y, text)
        y -= line

    write("=" * 29, center=True)
    write("CLUB NO. 1", size=12, center=True)
    write("=" * 29, center=True)
    write(f"Date:           {bill.generated_at:%Y-%m-%d}")
    write(f"Transaction ID: {bill.transaction_id}")
    write(f"Waiter:         {order.waiter.name}")
    write(f"Customer:       {order.customer.name if order.customer else '-'}")
    write("-" * 29)
    for item in order.items:
        label = f"{item.quantity}x {item.product.name}"
        amount = f"${item.quantity * float(item.unit_price):.2f}"
        write(f"{label:<20}{amount:>9}")
    write("-" * 29)
    write(f"{'TOTAL:':<20}{'$' + format(float(bill.total), '.2f'):>9}")
    write("=" * 29, center=True)
    write("Merci et a bientot!", center=True)
    write("=" * 29, center=True)

    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={bill.transaction_id}.pdf"},
    )
