import os
from fastapi import FastAPI
from app.routes import user_routes
from app.database import Base, engine
from fastapi.staticfiles import StaticFiles

UPLOADS_DIR = "uploads"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Afrovogue Commercial API", version="1.0")

# Ensure the uploads directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.include_router(user_routes.router)

app.mount(f"/{UPLOADS_DIR}", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/")
def root():
    return {"message": "Afrovogue API running"}
