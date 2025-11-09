# Afrovogue Commercial API — Local setup (PostgreSQL)

This README shows the minimal steps to run the API locally using PostgreSQL on Windows PowerShell.

1) Create a Python virtual environment and install dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Create a PostgreSQL database

- Using psql (example):

```powershell
# run psql and create DB (replace user/password as needed)
psql -U postgres -c "CREATE DATABASE afrovogue_db;"
```

Or use pgAdmin / Docker. Example Docker command:

```powershell
docker run --name afrovogue-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=afrovogue_db -p 5432:5432 -d postgres:15
```

3) Configure environment variables

Copy `.env.example` to `.env` and update the values:

```powershell
copy .env.example .env
# then edit .env with a text editor to set a secure JWT_SECRET
```

4) Run database migrations (alembic)

```powershell
alembic upgrade head
```

If alembic is not configured you can create tables directly (development only):

```powershell
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

5) Start the app

```powershell
uvicorn app.main:app --reload
```

6) API endpoints

- Register: POST /users/register
- Login: POST /users/login
- Products: /products

Notes
- `DATABASE_URL` should be in the format: postgresql://user:password@host:port/dbname
- Keep `JWT_SECRET` secret in production. Use a secure random string.

# afro-vogue-Backend