from app.database import engine
from app.models import Base
# Import models to ensure they are registered with Base metadata before creation
import app.models

def init():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating database tables if they do not exist...")
    try:
        init()
        print("Database initialization complete.")
    except Exception as e:
        print(f"Error initializing database: {e}")