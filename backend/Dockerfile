FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

EXPOSE 8000

# Railway (and similar PaaS) assign the listen port via $PORT at runtime;
# fall back to 8000 for local `docker compose up`. Migrations run before
# the app starts — schema changes now go through Alembic, not create_all().
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
