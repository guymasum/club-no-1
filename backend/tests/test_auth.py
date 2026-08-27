import pytest

from tests.conftest import auth_headers


async def test_login_success_returns_token(client, seeded):
    resp = await client.post("/auth/login", json={"username": "josee", "password": "clubno1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["role"] == "admin"
    assert body["name"] == "Josee"


async def test_login_wrong_password_rejected(client, seeded):
    resp = await client.post("/auth/login", json={"username": "josee", "password": "wrong"})
    assert resp.status_code == 401


async def test_login_unknown_user_rejected(client, seeded):
    resp = await client.post("/auth/login", json={"username": "nobody", "password": "clubno1"})
    assert resp.status_code == 401


async def test_protected_route_requires_token(client, seeded):
    resp = await client.get("/customers")
    assert resp.status_code == 401


async def test_admin_route_rejects_waiter_role(client, seeded):
    resp = await client.post("/auth/login", json={"username": "mimi", "password": "clubno1"})
    token = resp.json()["access_token"]
    resp = await client.post(
        "/admin/products",
        json={"name": "New dish", "category": "food", "price": 5.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_admin_route_allows_admin_role(client, seeded):
    resp = await client.post("/auth/login", json={"username": "josee", "password": "clubno1"})
    token = resp.json()["access_token"]
    resp = await client.post(
        "/admin/products",
        json={"name": "New dish", "category": "food", "price": 5.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201


async def test_admin_product_list_includes_inactive(client, seeded):
    headers = await auth_headers(client, "josee")
    food_id = seeded["food"].product_id

    await client.put(f"/admin/products/{food_id}", json={"active": False}, headers=headers)

    # The waiter-facing catalog hides it...
    resp = await client.get("/products", headers=headers)
    assert all(p["product_id"] != food_id for p in resp.json())

    # ...but the admin listing still shows it, so it can be reactivated.
    resp = await client.get("/admin/products", headers=headers)
    assert resp.status_code == 200
    matching = [p for p in resp.json() if p["product_id"] == food_id]
    assert matching and matching[0]["active"] is False


async def test_waiter_can_change_own_password(client, seeded):
    headers = await auth_headers(client, "mimi")

    resp = await client.put(
        "/auth/password",
        json={"current_password": "clubno1", "new_password": "nouveaumdp"},
        headers=headers,
    )
    assert resp.status_code == 204

    resp = await client.post("/auth/login", json={"username": "mimi", "password": "clubno1"})
    assert resp.status_code == 401

    resp = await client.post("/auth/login", json={"username": "mimi", "password": "nouveaumdp"})
    assert resp.status_code == 200


async def test_change_password_rejects_wrong_current_password(client, seeded):
    headers = await auth_headers(client, "mimi")
    resp = await client.put(
        "/auth/password",
        json={"current_password": "wrong", "new_password": "nouveaumdp"},
        headers=headers,
    )
    assert resp.status_code == 401

    # Original password must still work.
    resp = await client.post("/auth/login", json={"username": "mimi", "password": "clubno1"})
    assert resp.status_code == 200


async def test_change_password_rejects_too_short(client, seeded):
    headers = await auth_headers(client, "mimi")
    resp = await client.put(
        "/auth/password", json={"current_password": "clubno1", "new_password": "abc"}, headers=headers
    )
    assert resp.status_code == 422


async def test_admin_can_set_another_waiters_password(client, seeded):
    admin_headers = await auth_headers(client, "josee")
    waiter_id = seeded["waiter"].waiter_id

    resp = await client.put(f"/admin/waiters/{waiter_id}", json={"password": "motdepasseadmin"}, headers=admin_headers)
    assert resp.status_code == 200

    resp = await client.post("/auth/login", json={"username": "mimi", "password": "clubno1"})
    assert resp.status_code == 401

    resp = await client.post("/auth/login", json={"username": "mimi", "password": "motdepasseadmin"})
    assert resp.status_code == 200


async def test_waiter_role_cannot_set_another_waiters_password(client, seeded):
    headers = await auth_headers(client, "mimi")
    resp = await client.put(
        f"/admin/waiters/{seeded['admin'].waiter_id}", json={"password": "hacked"}, headers=headers
    )
    assert resp.status_code == 403
