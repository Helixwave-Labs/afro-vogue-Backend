from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/wishlist",
    tags=["Wishlist"]
)

@router.post("/products/{product_id}", status_code=status.HTTP_201_CREATED, response_model=schemas.CartProductOut)
def add_to_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Add a product to the current user's wishlist.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    wishlist_item = models.WishlistItem(user_id=current_user.id, product_id=product_id)

    try:
        db.add(wishlist_item)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already in wishlist.")

    # Return the product that was added, which is more efficient
    return product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Remove a product from the current user's wishlist.
    """
    wishlist_item = db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == current_user.id,
        models.WishlistItem.product_id == product_id
    ).first()

    if not wishlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in wishlist.")

    db.delete(wishlist_item)
    db.commit()

    return

@router.get("/", response_model=schemas.WishlistOut)
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Retrieve all products in the current user's wishlist.
    """
    # Eagerly load the product details for each wishlist item
    wishlist_items = db.query(models.WishlistItem).options(
        joinedload(models.WishlistItem.product)
    ).filter(models.WishlistItem.user_id == current_user.id).all()

    # Extract the product objects from the wishlist items
    products = [item.product for item in wishlist_items]

    return {"products": products}