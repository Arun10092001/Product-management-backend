import os
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import engine, session
from app import models
from app.routers import user, product, category
from app import auth

load_dotenv()

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Product API", description="A REST API for products and users")

app.add_middleware(
    CORSMiddleware,
    # Allow all origins during development so frontend can reach the API
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(product.router)
app.include_router(category.router)

from sqlalchemy import text

# Initialize database with some products if empty
def init_db():
    db = session()
    try:
        # Auto-migrate: Drop category string and add category_id (best-effort)
        try:
            db.execute(text("ALTER TABLE product DROP COLUMN category"))
            db.execute(text("ALTER TABLE product ADD COLUMN category_id INTEGER"))
            db.execute(text("ALTER TABLE product ADD CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category (id)"))
            db.commit()
        except Exception:
            db.rollback()  # Columns likely already updated or DB doesn't support the operation

        # Insert default categories if none exist
        count_cats = db.query(models.Category).count()
        if count_cats == 0:
            default_categories = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Others"]
            for c_name in default_categories:
                db.add(models.Category(name=c_name))
            db.commit()

        # Seed some default products if none exist
        count = db.query(models.Product).count()
        if count == 0:
            products = [
                models.Product(name="Iphone", description="I bought that yesterday", price=99.50, quantity=5),
                models.Product(name="MacBook", description="I bought that yesterday", price=1400.00, quantity=3),
            ]
            db.add_all(products)
            db.commit()

        # Seed admin user if none exists
        try:
            # Ensure `role` column exists on users table (for upgrades from older schema)
            try:
                db.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR"))
                db.commit()
            except Exception:
                db.rollback()
            # Populate missing roles and make column have a default
            try:
                db.execute(text("UPDATE users SET role='customer' WHERE role IS NULL"))
                db.execute(text("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'customer'"))
                db.execute(text("ALTER TABLE users ALTER COLUMN role SET NOT NULL"))
                db.commit()
            except Exception:
                db.rollback()

            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            existing_admin = db.query(models.User).filter(models.User.username == admin_username).first()
            if not existing_admin:
                admin_user = models.User(
                    username=admin_username,
                    email=f"{admin_username}@example.com",
                    hashed_password=auth.hash_password(admin_password),
                    role="admin",
                )
                db.add(admin_user)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()
init_db()

@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI Product API. Visit /docs for Swagger UI."}
