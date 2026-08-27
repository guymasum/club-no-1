from app.models import Product, StockItem
from tests.conftest import auth_headers


async def _make_wine_stock(db_session):
    """5 portions/bottle, 2 bottles on hand = 10 portions. Bottle sale
    consumes 5 portions, glass sale consumes 1 — same pool."""
    stock = StockItem(name="Vin test", portions_per_container=5, quantity_on_hand=10)
    db_session.add(stock)
    await db_session.commit()
    await db_session.refresh(stock)

    glass = Product(name="Vin test (verre)", category="wine", price=3000, stock_item_id=stock.stock_item_id, portions_per_sale=1)
    bottle = Product(name="Vin test (bouteille)", category="wine", price=12000, stock_item_id=stock.stock_item_id, portions_per_sale=5)
    db_session.add_all([glass, bottle])
    await db_session.commit()
    await db_session.refresh(glass)
    await db_session.refresh(bottle)
    return stock, glass, bottle


async def test_admin_can_create_stock_item_and_link_product(client, seeded):
    headers = await auth_headers(client, "josee")

    resp = await client.post(
        "/admin/stock-items",
        json={"name": "Whisky test", "portions_per_container": 15, "quantity_on_hand": 15},
        headers=headers,
    )
    assert resp.status_code == 201
    stock_item_id = resp.json()["stock_item_id"]

    resp = await client.post(
        "/admin/products",
        json={
            "name": "Whisky test (verre)",
            "category": "whisky",
            "price": 4000,
            "stock_item_id": stock_item_id,
            "portions_per_sale": 1,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["stock_item_id"] == stock_item_id
    assert body["stock_remaining"] == 15  # 15 portions / 1 per sale


async def test_selling_glass_and_bottle_share_the_same_stock_pool(client, seeded, db_session):
    stock, glass, bottle = await _make_wine_stock(db_session)
    headers = await auth_headers(client, "mimi")
    admin_headers = await auth_headers(client, "josee")

    resp = await client.post("/orders", json={}, headers=headers)
    order_id = resp.json()["order_id"]

    # Sell 2 glasses (2 portions) then 1 bottle (5 portions): 10 - 2 - 5 = 3 left.
    resp = await client.post(
        f"/orders/{order_id}/items", json={"product_id": glass.product_id, "quantity": 2}, headers=headers
    )
    assert resp.status_code == 201

    resp = await client.post(
        f"/orders/{order_id}/items", json={"product_id": bottle.product_id, "quantity": 1}, headers=headers
    )
    assert resp.status_code == 201

    resp = await client.get("/admin/stock-items", headers=admin_headers)
    updated = next(s for s in resp.json() if s["stock_item_id"] == stock.stock_item_id)
    assert updated["quantity_on_hand"] == 3

    # Product-level view: 3 portions left / 1 per glass = 3 glasses sellable;
    # 3 portions / 5 per bottle = 0 more full bottles sellable.
    resp = await client.get("/products", headers=headers)
    products = {p["product_id"]: p for p in resp.json()}
    assert products[glass.product_id]["stock_remaining"] == 3
    assert products[bottle.product_id]["stock_remaining"] == 0


async def test_cannot_oversell_beyond_available_stock(client, seeded, db_session):
    stock, glass, bottle = await _make_wine_stock(db_session)
    headers = await auth_headers(client, "mimi")

    resp = await client.post("/orders", json={}, headers=headers)
    order_id = resp.json()["order_id"]

    # Only 2 bottles' worth (10 portions) exist; asking for 3 bottles (15) must fail.
    resp = await client.post(
        f"/orders/{order_id}/items", json={"product_id": bottle.product_id, "quantity": 3}, headers=headers
    )
    assert resp.status_code == 400

    # Stock must be untouched by the rejected sale.
    admin_headers = await auth_headers(client, "josee")
    resp = await client.get("/admin/stock-items", headers=admin_headers)
    updated = next(s for s in resp.json() if s["stock_item_id"] == stock.stock_item_id)
    assert updated["quantity_on_hand"] == 10


async def test_removing_item_restocks_it(client, seeded, db_session):
    stock, glass, bottle = await _make_wine_stock(db_session)
    headers = await auth_headers(client, "mimi")
    admin_headers = await auth_headers(client, "josee")

    resp = await client.post("/orders", json={}, headers=headers)
    order_id = resp.json()["order_id"]

    resp = await client.post(
        f"/orders/{order_id}/items", json={"product_id": glass.product_id, "quantity": 4}, headers=headers
    )
    item_id = resp.json()["items"][0]["item_id"]

    resp = await client.get("/admin/stock-items", headers=admin_headers)
    assert next(s for s in resp.json() if s["stock_item_id"] == stock.stock_item_id)["quantity_on_hand"] == 6

    resp = await client.delete(f"/orders/{order_id}/items/{item_id}", headers=headers)
    assert resp.status_code == 200

    resp = await client.get("/admin/stock-items", headers=admin_headers)
    assert next(s for s in resp.json() if s["stock_item_id"] == stock.stock_item_id)["quantity_on_hand"] == 10


async def test_restock_endpoint_records_delivery_and_rejects_negative_result(client, seeded):
    headers = await auth_headers(client, "josee")
    resp = await client.post(
        "/admin/stock-items", json={"name": "Beer crate", "portions_per_container": 1, "quantity_on_hand": 5}, headers=headers
    )
    stock_item_id = resp.json()["stock_item_id"]

    resp = await client.post(f"/admin/stock-items/{stock_item_id}/restock", json={"delta": 24}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["quantity_on_hand"] == 29

    resp = await client.post(f"/admin/stock-items/{stock_item_id}/restock", json={"delta": -100}, headers=headers)
    assert resp.status_code == 400


async def test_food_product_has_no_stock_tracking(client, seeded):
    headers = await auth_headers(client, "mimi")
    resp = await client.get("/products", headers=headers)
    food = next(p for p in resp.json() if p["category"] == "food")
    assert food["stock_item_id"] is None
    assert food["stock_remaining"] is None
