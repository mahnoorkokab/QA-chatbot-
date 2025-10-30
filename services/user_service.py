from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import UserDB, User
from auth import hash_password, verify_password, validate_password

async def register_user(user: User, db: Session):
    # Validate password length
    validate_password(user.password)

    # Check if email already exists
    existing = db.query(UserDB).filter(UserDB.username == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed = hash_password(user.password)

    # Create new user in DB
    new_user = UserDB(username=user.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return email + original password + message (for demo/testing only)
    return {"email": new_user.username, "password": user.password, "msg": "Registration successful"}

async def authenticate_user(user: User, db: Session):
    # Fetch user by email
    db_user = db.query(UserDB).filter(UserDB.username == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Return email + original password + message (for demo/testing only)
    return {"email": db_user.username, "password": user.password, "msg": "Authentication successful"}
