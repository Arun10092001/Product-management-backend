import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=schemas.PaginatedProducts)
def get_all_products(
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    category_id: Optional[int] = None,
    page: int = 1,
    limit: int = 9,
    db: Session = Depends(auth.get_db),
):
    page = max(page, 1)
    limit = max(limit, 1)

    query = db.query(models.Product)

    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))

    if category_id:
        query = query.filter(models.Product.category_id == category_id)

    total = query.count()

    if sort_by == "price_asc":
        query = query.order_by(models.Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(models.Product.price.desc())
    elif sort_by == "name_asc":
        query = query.order_by(models.Product.name.asc())
    elif sort_by == "name_desc":
        query = query.order_by(models.Product.name.desc())

    items = query.offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "items": items}

@router.get("/{id}", response_model=schemas.Product)
def get_product(id: int, db: Session = Depends(auth.get_db)):
    db_product = db.query(models.Product).filter(
        models.Product.id == id).first()
    if db_product:
        return db_product

    raise HTTPException(status_code=404, detail="Product not found")

@router.post("", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(auth.get_db), _admin: models.User = Depends(auth.require_admin)):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/{id}")
def update_product(id: int, product: schemas.ProductCreate, db: Session = Depends(auth.get_db), _admin: models.User = Depends(auth.require_admin)):
    db_product = db.query(models.Product).filter(
        models.Product.id == id).first()
    if db_product:
        db_product.name = product.name
        db_product.description = product.description
        db_product.price = product.price
        db_product.quantity = product.quantity
        db.commit()
        return {"message": "Product updated"}
    else:
        raise HTTPException(status_code=404, detail="Product not found")

@router.delete("/{id}")
def delete_product(id: int, db: Session = Depends(auth.get_db), _admin: models.User = Depends(auth.require_admin)):
    db_product = db.query(models.Product).filter(
        models.Product.id == id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return {"message": "Product deleted"}
    else:
        raise HTTPException(status_code=404, detail="Product not found")
