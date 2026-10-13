from app.models import Bill, Customer, Order
from tests.conftest import auth_headers


async def test_create_customer_normalizes_phone_to_e164(client, seeded):
    headers = await auth_headers(client, "josee")
    resp = await client.post(
        "/admin/customers",
        json={"name": "Jean", "email": "jean@example.com", "phone": "79123456"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "jean@example.com"
    # "79123456" has no country code -> normalized against the BI default region.
    assert body["phone"] == "+25779123456"


async def test_create_customer_rejects_invalid_email(client, seeded):
    headers = await auth_headers(client, "josee")
    resp = await client.post(
        "/admin/customers", json={"name": "Jean", "email": "not-an-email"}, headers=headers
    )
    assert resp.status_code == 422


async def test_create_customer_rejects_unparseable_phone(client, seeded):
    headers = await auth_headers(client, "josee")
    resp = await client.post("/admin/customers", json={"name": "Jean", "phone": "abc"}, headers=headers)
    assert resp.status_code == 422


async def test_create_customer_without_contact_info_still_works(client, seeded):
    headers = await auth_headers(client, "josee")
    resp = await client.post("/admin/customers", json={"name": "Client de passage"}, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] is None
    assert body["phone"] is None


async def _billed_order_for_customer(client, db_session, seeded, headers, customer: Customer) -> dict:
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    resp = await client.post("/orders", json={"customer_id": customer.customer_id}, headers=headers)
    order_id = resp.json()["order_id"]
    food_id = seeded["food"].product_id
    await client.post(f"/orders/{order_id}/items", json={"product_id": food_id, "quantity": 1}, headers=headers)
    resp = await client.post(f"/orders/{order_id}/bill", headers=headers)
    return resp.json()


async def test_send_email_without_customer_email_returns_400(client, seeded, db_session):
    headers = await auth_headers(client, "mimi")
    customer = Customer(name="Jean")  # no email
    bill = await _billed_order_for_customer(client, db_session, seeded, headers, customer)

    resp = await client.post(f"/bills/{bill['bill_id']}/send-email", headers=headers)
    assert resp.status_code == 400


async def test_send_email_success_updates_status_to_sent(client, seeded, db_session, monkeypatch):
    sent = {}

    def fake_send_email(*, to, subject, body, attachment, attachment_filename):
        sent["to"] = to
        sent["attachment_len"] = len(attachment)

    monkeypatch.setattr("app.routers.bills.send_email", fake_send_email)

    headers = await auth_headers(client, "mimi")
    customer = Customer(name="Jean", email="jean@example.com")
    bill = await _billed_order_for_customer(client, db_session, seeded, headers, customer)

    resp = await client.post(f"/bills/{bill['bill_id']}/send-email", headers=headers)
    assert resp.status_code == 202
    assert resp.json()["email_status"] == "pending"

    # httpx's ASGITransport awaits the whole request, BackgroundTasks
    # included, before returning — so the task has already finished here.
    resp = await client.get(f"/bills/{bill['bill_id']}", headers=headers)
    assert resp.json()["email_status"] == "sent"
    assert sent["to"] == "jean@example.com"
    assert sent["attachment_len"] > 0


async def test_send_email_failure_records_error_and_is_retryable(client, seeded, db_session, monkeypatch):
    from app.email_utils import EmailSendError

    call_count = {"n": 0}

    def flaky_send_email(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise EmailSendError("Connexion SMTP refusée")

    monkeypatch.setattr("app.routers.bills.send_email", flaky_send_email)

    headers = await auth_headers(client, "mimi")
    customer = Customer(name="Jean", email="jean@example.com")
    bill = await _billed_order_for_customer(client, db_session, seeded, headers, customer)

    resp = await client.post(f"/bills/{bill['bill_id']}/send-email", headers=headers)
    assert resp.status_code == 202
    resp = await client.get(f"/bills/{bill['bill_id']}", headers=headers)
    body = resp.json()
    assert body["email_status"] == "failed"
    assert "SMTP" in body["email_error"]

    # Staff can just click "send" again — nothing about the failure blocks a retry.
    resp = await client.post(f"/bills/{bill['bill_id']}/send-email", headers=headers)
    assert resp.status_code == 202
    resp = await client.get(f"/bills/{bill['bill_id']}", headers=headers)
    assert resp.json()["email_status"] == "sent"
