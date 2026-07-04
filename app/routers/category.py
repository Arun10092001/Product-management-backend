from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, auth

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(auth.get_db)):
    return db.query(models.Category).all()


@router.post("", response_model=schemas.Category)
def create_category(category_in: schemas.CategoryCreate, db: Session = Depends(auth.get_db), _admin: models.User = Depends(auth.require_admin)):
    existing = db.query(models.Category).filter(models.Category.name == category_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    cat = models.Category(name=category_in.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{id}")
def update_category(id: int, category_in: schemas.CategoryCreate, db: Session = Depends(auth.get_db), _admin: models.User = Depends(auth.require_admin)):
    db_cat = db.query(models.Category).filter(models.Category.id == id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db_cat.name = category_in.name
    db.commit()
    return {"message": "Category updated"}


@router.delete("/{id}")
def delete_category(id: int, db: Session = Depends(auth.get_db), _admin: models.User = Depends(auth.require_admin)):
    db_cat = db.query(models.Category).filter(models.Category.id == id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_cat)
    db.commit()
    return {"message": "Category deleted"}
