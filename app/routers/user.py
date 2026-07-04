import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import APIRouter, Depends, HTTPException
import traceback
import logging

logger = logging.getLogger("app.users")
from sqlalchemy.orm import Session
from app import models, schemas, auth

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.post("/register")
def register(user_in: schemas.UserCreate, db: Session = Depends(auth.get_db)):
    logger.info("Register attempt: %s", getattr(user_in, "username", None))
    try:
        existing = db.query(models.User).filter(
            (models.User.username == user_in.username) | (models.User.email == user_in.email)
        ).first()
    except Exception as e:
        logger.error("DB query failed: %s", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    if existing:
        raise HTTPException(
            status_code=400, detail="Username or email already taken"
        )

    user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=auth.hash_password(user_in.password),
        role="customer",
    )
    try:
        db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "User created successfully"}

@router.post("/login")
def login(user_in: schemas.UserLogin, db: Session = Depends(auth.get_db)):
    user = db.query(models.User).filter(
        models.User.username == user_in.username
    ).first()
    if not user or not auth.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth.create_access_token({"username": user.username, "user_id": user.id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}
