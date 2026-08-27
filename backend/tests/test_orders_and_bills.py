from tests.conftest import auth_headers


async def test_full_order_to_bill_flow(client, seeded):
    headers = await auth_headers(client, "mimi")

    resp = await client.get("/products", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.post("/orders", json={}, headers=headers)
    assert resp.status_code == 201
    order = resp.json()
    order_id = order["order_id"]
    assert order["status"] == "open"

    food_id = seeded["food"].product_id
    drink_id = seeded["drink"].product_id

    resp = await client.post(
        f"/orders/{order_id}/items", json={"product_id": food_id, "quantity": 2}, headers=headers
    )
    assert resp.status_code == 201

    resp = await client.post(
        f"/orders/{order_id}/items", json={"product_id": drink_id, "quantity": 1}, headers=headers
    )
    assert resp.status_code == 201
    order = resp.json()
    assert len(order["items"]) == 2

    item_to_remove = order["items"][0]["item_id"]
    resp = await client.delete(f"/orders/{order_id}/items/{item_to_remove}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1

    resp = await client.post(
        f"/orders/{order_id}/items", json={"product_id": food_id, "quantity": 2}, headers=headers
    )
    assert resp.status_code == 201

    resp = await client.post(f"/orders/{order_id}/bill", headers=headers)
    assert resp.status_code == 201
    bill = resp.json()
    assert bill["transaction_id"].startswith("TXN-")
    assert bill["total"] == 16.0 + 3.0  # 2x food (8 each) + 1x drink
    assert bill["waiter_name"] == "Mimi"

    resp = await client.get(f"/bills/{bill['bill_id']}/pdf", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


async def test_cannot_bill_order_with_no_items(client, seeded):
    headers = await auth_headers(client, "mimi")
    resp = await client.post("/orders", json={}, headers=headers)
    order_id = resp.json()["order_id"]

    resp = await client.post(f"/orders/{order_id}/bill", headers=headers)
    assert resp.status_code == 400


async def test_cannot_add_items_to_billed_order(client, seeded):
    headers = await auth_headers(client, "mimi")
    resp = await client.post("/orders", json={}, headers=headers)
    order_id = resp.json()["order_id"]

    food_id = seeded["food"].product_id
    await client.post(f"/orders/{order_id}/items", json={"product_id": food_id, "quantity": 1}, headers=headers)
    await client.post(f"/orders/{order_id}/bill", headers=headers)

    resp = await client.post(f"/orders/{order_id}/items", json={"product_id": food_id, "quantity": 1}, headers=headers)
    assert resp.status_code == 400
