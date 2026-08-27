from app.models import Customer
from tests.conftest import auth_headers


async def test_admin_can_update_product_name_and_price(client, seeded):
    headers = await auth_headers(client, "josee")
    food_id = seeded["food"].product_id

    resp = await client.put(
        f"/admin/products/{food_id}",
        json={"name": "Brochettes de langues (grillées)", "price": 9500},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Brochettes de langues (grillées)"
    assert body["price"] == 9500


async def test_admin_can_rename_customer(client, seeded, db_session):
    headers = await auth_headers(client, "josee")
    customer = Customer(name="Jean")
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    resp = await client.put(
        f"/admin/customers/{customer.customer_id}", json={"name": "Jean-Pierre"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Jean-Pierre"


async def test_deleting_customer_falls_back_orders_to_walkin(client, seeded, db_session):
    headers = await auth_headers(client, "mimi")
    customer = Customer(name="Jean")
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    resp = await client.post("/orders", json={"customer_id": customer.customer_id}, headers=headers)
    order_id = resp.json()["order_id"]

    admin_headers = await auth_headers(client, "josee")
    resp = await client.delete(f"/admin/customers/{customer.customer_id}", headers=admin_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/orders/{order_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["customer_id"] is None
    assert resp.json()["customer_name"] is None


async def test_deactivated_waiter_cannot_login_or_use_existing_token(client, seeded):
    headers = await auth_headers(client, "mimi")
    admin_headers = await auth_headers(client, "josee")

    resp = await client.put(
        f"/admin/waiters/{seeded['waiter'].waiter_id}", json={"active": False}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["active"] is False

    # Fresh login is rejected...
    resp = await client.post("/auth/login", json={"username": "mimi", "password": "clubno1"})
    assert resp.status_code == 403

    # ...and the token issued before deactivation stops working immediately.
    resp = await client.get("/orders", headers=headers)
    assert resp.status_code == 401


async def test_cannot_remove_last_active_admin(client, seeded):
    headers = await auth_headers(client, "josee")
    resp = await client.put(
        f"/admin/waiters/{seeded['admin'].waiter_id}", json={"active": False}, headers=headers
    )
    assert resp.status_code == 400
