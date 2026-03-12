from sqlalchemy.orm import sessionmaker
from app.database import engine
from app import models, auth
import getpass

# Create a session factory using the existing engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_superuser():
    db = SessionLocal()
    try:
        print("--- Create Superuser ---")
        username = input("Username: ")
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm Password: ")

        if password != confirm_password:
            print("Error: Passwords do not match.")
            return

        # Check if user already exists
        existing_user = db.query(models.User).filter(
            (models.User.email == email) | (models.User.username == username)
        ).first()
        
        if existing_user:
            print(f"Error: User with email {email} or username {username} already exists.")
            return

        # Hash password and create user
        hashed_password = auth.hash_password(password)
        
        new_user = models.User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role="admin",  # This is the key field for superusers
            is_active=True,
            otp=None,
            otp_expires_at=None
        )
        
        db.add(new_user)
        db.commit()
        print(f"Success! Superuser '{username}' created.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_superuser()