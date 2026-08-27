# Club No. 1 — Restaurant Management App · System Design Document

## 1. Overview

**Club No. 1** is a small restaurant/club serving drinks (beers, wine) and 3 food dishes. This app manages waiter authentication, customer order entry, and bill generation.

**Users:** Waiters (Josée, Mimi, Victor + future additions)  
**Customers:** ~25 known regulars  
**Scale:** Very small; 3 concurrent waiters max at launch

---

## 2. Locked Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Frontend | React | Familiar, component-friendly for order UI |
| Backend | Python + FastAPI | Clean REST API; good PDF libs (weasyprint/reportlab) |
| Database | PostgreSQL | Relational, free on Railway/Render |
| Hosting | Railway (starter ~$5–7/mo) | Always-on, Docker-friendly, cheap |
| Deployment | Docker (single docker-compose) | Portable, Railway supports it natively |
| Auth | JWT + bcrypt hashed passwords | No plain text; role-based (waiter / admin) |

---

## 3. Database Schema

```sql
-- Waiters (also serve as app users)
CREATE TABLE waiters (
  waiter_id   SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  username    TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role        TEXT NOT NULL DEFAULT 'waiter',  -- 'waiter' | 'admin'
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Known customers
CREATE TABLE customers (
  customer_id SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Products (beers, wine, food dishes)
CREATE TABLE products (
  product_id  SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  category    TEXT NOT NULL,  -- 'drink' | 'food'
  price       NUMERIC(10,2) NOT NULL,
  active      BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Orders (one per table visit / transaction)
CREATE TABLE orders (
  order_id    SERIAL PRIMARY KEY,
  waiter_id   INT REFERENCES waiters(waiter_id),
  customer_id INT REFERENCES customers(customer_id),
  status      TEXT NOT NULL DEFAULT 'open',  -- 'open' | 'billed'
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Order line items
CREATE TABLE order_items (
  item_id     SERIAL PRIMARY KEY,
  order_id    INT REFERENCES orders(order_id),
  product_id  INT REFERENCES products(product_id),
  quantity    INT NOT NULL,
  unit_price  NUMERIC(10,2) NOT NULL
);

-- Bills (finalized, printable)
CREATE TABLE bills (
  bill_id        SERIAL PRIMARY KEY,
  order_id       INT REFERENCES orders(order_id),
  transaction_id TEXT UNIQUE NOT NULL,
  total          NUMERIC(10,2) NOT NULL,
  generated_at   TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. Seed Data

### Waiters
| Name | Username | Role |
|------|----------|------|
| Josée | josee | waiter |
| Mimi | mimi | waiter |
| Victor | victor | waiter |

### Products
| Name | Category |
|------|----------|
| Brochettes de langues | food |
| Brochette de musoso | food |
| Brochettes de poisson | food |

---

## 5. Feature Slices (ordered thin to thick)

### Slice 1 — Auth (vertical spine)
- `POST /auth/login` returns JWT
- JWT middleware on all protected routes
- Role guard: admin routes reject waiter role

### Slice 2 — Order Entry
- `GET /customers` list all customers
- `GET /products` list active products
- `POST /orders` create order (waiter_id from JWT)
- `POST /orders/{id}/items` add item to order
- `DELETE /orders/{id}/items/{item_id}` remove item

### Slice 3 — Bill Generation
- `POST /orders/{id}/bill` finalise order, create bill, generate transaction_id
- Bill includes: date, transaction_id, waiter name, customer name, line items, total
- `GET /bills/{id}/pdf` optional PDF download

### Slice 4 — Admin Panel
- `POST /waiters` add waiter (admin only)
- `PUT /waiters/{id}` update waiter
- `POST /products` add product (admin only)
- `PUT /products/{id}` update/deactivate product
- `POST /customers` add customer

### Slice 5 — Frontend (React SPA)
- Login screen
- Waiter dashboard: select customer, browse products, build order, generate bill
- Admin dashboard: manage waiters, products, customers
- Bill view: printable receipt layout

---

## 6. Bill Format

```
==================================
           CLUB NO. 1
==================================
Date:           2026-08-27
Transaction ID: TXN-20260827-0042
Waiter:         Josee
Customer:       Jean-Pierre
----------------------------------
2x Brochettes de langues   16 000 FBu
1x Beer                     3 000 FBu
----------------------------------
TOTAL:                     19 000 FBu
==================================
     Merci et a bientot!
==================================
```

Currency: Burundian Franc (BIF), displayed as "FBu" per local convention.
BIF has no minor unit in everyday use, so amounts are whole numbers with
a space thousands-separator (no decimals).

---

## 7. Non-Functional Requirements

- Password hashing: bcrypt cost factor 12
- JWT expiry: 8 hours (one shift)
- Docker Compose: web (FastAPI) + db (PostgreSQL) services
- Environment variables: DATABASE_URL, SECRET_KEY, ENVIRONMENT
- Bills generated on-demand from DB; no file storage needed

---

## 8. Out of Scope (v1)

- Payment processing
- Inventory tracking
- Shift reports or analytics
- Mobile native app (responsive web sufficient)
