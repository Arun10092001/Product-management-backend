from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    quantity: int
    category_id: Optional[int] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    category: Optional[Category] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedProducts(BaseModel):
    items: List[Product]
    total: int
