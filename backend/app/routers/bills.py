import asyncio
import io
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import database
from app.database import get_db
from app.deps import get_current_waiter
from app.email_utils import EmailSendError, send_email
from app.models import Bill, Order, OrderItem
from app.schemas import BillOut, BillSummaryOut, OrderItemOut, SendBillEmailOut

router = APIRouter(tags=["bills"], dependencies=[Depends(get_current_waiter)])

logger = logging.getLogger(__name__)

RECEIPT_WIDTH = 80 * mm


def format_bif(amount: float) -> str:
    """BIF has no minor unit in everyday use, so amounts are whole numbers
    with a space thousands-separator, e.g. 15000 -> '15 000 FBu'."""
    return f"{amount:,.0f}".replace(",", " ") + " FBu"


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
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Commande introuvable")
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
        customer_email=order.customer.email if order.customer else None,
        email_status=bill.email_status,
        email_error=bill.email_error,
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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Commande déjà facturée")
    if not order.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Impossible de facturer une commande sans articles")

    total = sum(item.quantity * float(item.unit_price) for item in order.items)
    transaction_id = f"TXN-{datetime.now(UTC):%Y%m%d}-{order.order_id:04d}"

    bill = Bill(order_id=order.order_id, transaction_id=transaction_id, total=total)
    order.status = "billed"
    db.add(bill)
    await db.commit()
    await db.refresh(bill)

    return _bill_to_out(bill, order)


@router.get("/bills", response_model=list[BillSummaryOut])
async def list_bills(db: AsyncSession = Depends(get_db)) -> list[BillSummaryOut]:
    result = await db.execute(
        select(Bill)
        .options(
            selectinload(Bill.order).selectinload(Order.waiter),
            selectinload(Bill.order).selectinload(Order.customer),
        )
        .order_by(Bill.generated_at.desc())
    )
    bills = result.scalars().all()
    return [
        BillSummaryOut(
            bill_id=bill.bill_id,
            transaction_id=bill.transaction_id,
            total=float(bill.total),
            generated_at=bill.generated_at,
            waiter_name=bill.order.waiter.name,
            customer_name=bill.order.customer.name if bill.order.customer else None,
        )
        for bill in bills
    ]


@router.get("/bills/{bill_id}", response_model=BillOut)
async def get_bill(bill_id: int, db: AsyncSession = Depends(get_db)) -> BillOut:
    bill = await db.get(Bill, bill_id)
    if bill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Facture introuvable")
    order = await _load_order_for_bill(bill.order_id, db)
    return _bill_to_out(bill, order)


def _render_bill_pdf(bill: Bill, order: Order) -> bytes:
    """Shared by the download route and the email background task, so the
    emailed receipt is byte-for-byte the same PDF a waiter could download."""
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

    width = 34
    write("=" * width, center=True)
    write("CLUB NO. 1", size=12, center=True)
    write("=" * width, center=True)
    write(f"{'Date :':<20}{bill.generated_at:%Y-%m-%d}")
    write(f"{'N° de transaction :':<20}{bill.transaction_id}")
    write(f"{'Serveur :':<20}{order.waiter.name}")
    write(f"{'Client :':<20}{order.customer.name if order.customer else '-'}")
    write("-" * width)
    for item in order.items:
        label = f"{item.quantity}x {item.product.name}"
        amount = format_bif(item.quantity * float(item.unit_price))
        write(f"{label:<20}{amount:>14}")
    write("-" * width)
    write(f"{'TOTAL :':<20}{format_bif(float(bill.total)):>14}")
    write("=" * width, center=True)
    write("Merci et à bientôt !", center=True)
    write("=" * width, center=True)

    pdf.save()
    buffer.seek(0)
    return buffer.read()


@router.get("/bills/{bill_id}/pdf")
async def get_bill_pdf(bill_id: int, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    bill = await db.get(Bill, bill_id)
    if bill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Facture introuvable")
    order = await _load_order_for_bill(bill.order_id, db)

    pdf_bytes = _render_bill_pdf(bill, order)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={bill.transaction_id}.pdf"},
    )


async def send_receipt_email_task(bill_id: int) -> None:
    """Runs as a FastAPI BackgroundTask, i.e. *after* the HTTP response for
    POST /bills/{id}/send-email has already been returned. Two things that
    matter here and don't apply to a normal request handler:

    1. The request's AsyncSession is already closed by the time this runs,
       so it opens its own fresh session rather than reusing one from
       Depends(get_db).
    2. Nothing awaits this task's result, so if send_email() raises and we
       didn't catch it, the exception would just vanish into asyncio's
       default handler (logged, if you're watching, and nobody — staff or
       customer — would ever know the email failed). The try/except below
       is what turns that silent failure into a visible email_status.

    Accessed as `database.AsyncSessionLocal()` (module attribute, looked up
    at call time) rather than imported directly — tests monkeypatch that
    attribute to point at the in-memory test engine, same as the dependency
    override they already do for get_db. `from app.database import
    AsyncSessionLocal` would copy the reference at import time and silently
    keep using the real Postgres engine no matter what the test overrides.
    """
    async with database.AsyncSessionLocal() as db:
        bill = await db.get(Bill, bill_id)
        if bill is None:
            return
        order = await _load_order_for_bill(bill.order_id, db)

        if order.customer is None or not order.customer.email:
            bill.email_status = "failed"
            bill.email_error = "Ce client n'a pas d'adresse e-mail enregistrée"
            await db.commit()
            return

        pdf_bytes = _render_bill_pdf(bill, order)

        try:
            # send_email() is blocking SMTP I/O — run it off the event loop
            # so it can't stall every other request in flight.
            await asyncio.to_thread(
                send_email,
                to=order.customer.email,
                subject=f"Votre reçu Club No. 1 — {bill.transaction_id}",
                body=(
                    f"Bonjour {order.customer.name},\n\n"
                    f"Veuillez trouver ci-joint votre reçu {bill.transaction_id} "
                    f"d'un montant de {format_bif(float(bill.total))}.\n\n"
                    "Merci et à bientôt !\nClub No. 1"
                ),
                attachment=pdf_bytes,
                attachment_filename=f"{bill.transaction_id}.pdf",
            )
        except EmailSendError as exc:
            logger.warning("Receipt email failed for bill %s: %s", bill_id, exc)
            bill.email_status = "failed"
            bill.email_error = str(exc)[:500]
        else:
            bill.email_status = "sent"
            bill.email_error = None
            bill.email_sent_at = datetime.now(UTC)
        await db.commit()


@router.post("/bills/{bill_id}/send-email", response_model=SendBillEmailOut, status_code=status.HTTP_202_ACCEPTED)
async def send_bill_email(
    bill_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> SendBillEmailOut:
    """On-demand only — nothing sends automatically when a bill is
    finalized. A waiter/admin clicks "send" in the UI, which calls this."""
    bill = await db.get(Bill, bill_id)
    if bill is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Facture introuvable")
    order = await _load_order_for_bill(bill.order_id, db)

    if order.customer is None or not order.customer.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ce client n'a pas d'adresse e-mail enregistrée")

    bill.email_status = "pending"
    bill.email_error = None
    await db.commit()

    background_tasks.add_task(send_receipt_email_task, bill.bill_id)
    return SendBillEmailOut(email_status="pending")
