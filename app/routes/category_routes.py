from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

def check_admin(current_user: models.User = Depends(auth.get_current_user)):
    """Dependency to check if the current user is an admin."""
    if current_user.role != "admin":  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action."
        )

# --- Category Endpoints ---

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CategoryOut, dependencies=[Depends(check_admin)])
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """
    Create a new product category. (Admin only)
    """
    db_category: Optional[models.Category] = db.query(models.Category).filter(models.Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    new_category = models.Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/", response_model=List[schemas.CategoryOut])
def get_all_categories(db: Session = Depends(get_db)):
    """
    Get a list of all categories and their subcategories. (Public)
    """
    categories = db.query(models.Category).all()
    return categories

@router.put("/{category_id}", response_model=schemas.CategoryOut, dependencies=[Depends(check_admin)])
def update_category(category_id: int, category_update: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """
    Update a category's name. (Admin only)
    """
    db_category: Optional[models.Category] = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if new name is already taken by another category
    existing_category: Optional[models.Category] = db.query(models.Category).filter(models.Category.name == category_update.name, models.Category.id != category_id).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name already in use")

    db_category.name = category_update.name  # type: ignore
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(check_admin)])
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    Delete a category and all its subcategories. (Admin only)
    """
    db_category: Optional[models.Category] = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    return

# --- SubCategory Endpoints ---

@router.post("/{category_id}/subcategories", status_code=status.HTTP_201_CREATED, response_model=schemas.SubCategoryOut, dependencies=[Depends(check_admin)])
def create_subcategory(category_id: int, subcategory: schemas.SubCategoryCreate, db: Session = Depends(get_db)):
    """
    Create a new subcategory within a specific category. (Admin only)
    """
    db_category: Optional[models.Category] = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Parent category not found")
    
    new_subcategory = models.SubCategory(**subcategory.model_dump(), category_id=category_id)
    db.add(new_subcategory)
    db.commit()
    db.refresh(new_subcategory)
    return new_subcategory

@router.put("/subcategories/{subcategory_id}", response_model=schemas.SubCategoryOut, dependencies=[Depends(check_admin)])
def update_subcategory(subcategory_id: int, subcategory_update: schemas.SubCategoryCreate, db: Session = Depends(get_db)):
    """
    Update a subcategory's name. (Admin only)
    """
    db_subcategory: Optional[models.SubCategory] = db.query(models.SubCategory).filter(models.SubCategory.id == subcategory_id).first()
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    
    db_subcategory.name = subcategory_update.name  # type: ignore
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory

@router.delete("/subcategories/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(check_admin)])
def delete_subcategory(subcategory_id: int, db: Session = Depends(get_db)):
    """
    Delete a subcategory. (Admin only)
    """
    db_subcategory: Optional[models.SubCategory] = db.query(models.SubCategory).filter(models.SubCategory.id == subcategory_id).first()
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    db.delete(db_subcategory)
    db.commit()
    return