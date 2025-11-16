from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/cart",
    tags=["Shopping Cart"]
)

def get_or_create_cart(db: Session, user_id: int) -> models.Cart:
    """Helper function to retrieve a user's cart, creating it if it doesn't exist."""
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        cart = models.Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

@router.get("/", response_model=schemas.CartOut)
def get_user_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Retrieve the current user's shopping cart.
    """
    cart = db.query(models.Cart).options(
        joinedload(models.Cart.items).joinedload(models.CartItem.product)
    ).filter(models.Cart.user_id == current_user.id).first()

    if not cart or not cart.items:
        return {"items": [], "total_price": 0.0, "total_items": 0}

    total_price = sum(item.product.price * item.quantity for item in cart.items)
    total_items = sum(item.quantity for item in cart.items)

    return {"items": cart.items, "total_price": total_price, "total_items": total_items}

@router.post("/items", response_model=schemas.CartOut)
def add_item_to_cart(
    item_data: schemas.CartItemAdd,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Add a product to the cart or update its quantity if it already exists.
    """
    if item_data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be a positive integer.")

    cart = get_or_create_cart(db, current_user.id)

    # Check if product exists
    product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Check if item is already in the cart
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == cart.id,
        models.CartItem.product_id == item_data.product_id
    ).first()

    if cart_item:
        # Update quantity
        cart_item.quantity = item_data.quantity
    else:
        # Add new item
        cart_item = models.CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity
        )
        db.add(cart_item)

    db.commit()
    # Use the get_user_cart function to return the updated cart state
    return get_user_cart(db, current_user)

@router.delete("/items/{product_id}", response_model=schemas.CartOut)
def remove_item_from_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Remove a specific product from the user's cart.
    """
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found.")

    cart_item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == cart.id,
        models.CartItem.product_id == product_id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not found in cart.")

    db.delete(cart_item)
    db.commit()
    return get_user_cart(db, current_user)

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Remove all items from the user's cart.
    """
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if cart:
        # This leverages the `cascade="all, delete-orphan"` on the Cart.items relationship
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
        db.commit()
    return