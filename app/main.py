import os
from fastapi import FastAPI # type: ignore
import redis.asyncio as redis # type: ignore
from app.routes import user_routes, product_routes, category_routes, cart_routes, order_routes, review_routes, wishlist_routes
from app.database import Base, engine
from fastapi.staticfiles import StaticFiles # type: ignore
from fastapi_limiter import FastAPILimiter # type: ignore

app = FastAPI(title="Afrovogue Commercial API", version="1.0")

@app.on_event("startup")
async def startup():
    """Initialize the rate limiter on application startup."""
    redis_conn = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_conn)

app.include_router(user_routes.router)
app.include_router(product_routes.router)
app.include_router(category_routes.router)
app.include_router(cart_routes.router)
app.include_router(order_routes.router)
app.include_router(review_routes.router)
app.include_router(wishlist_routes.router)

# Mount the 'static' directory to serve profile pictures
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"message": "Afrovogue API running"}
