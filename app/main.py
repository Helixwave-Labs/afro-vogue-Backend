from fastapi import FastAPI
from app.routes import user_routes
from app.database import Base, engine
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Afrovogue Commercial API", version="1.0")

app.include_router(user_routes.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message": "Afrovogue API running"}
