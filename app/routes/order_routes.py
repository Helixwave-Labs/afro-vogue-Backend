from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.OrderOut)
def create_order_from_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Create an order from the user's current shopping cart.
    This will clear the cart upon successful order creation.
    """
    cart = db.query(models.Cart).options(
        joinedload(models.Cart.items).joinedload(models.CartItem.product)
    ).filter(models.Cart.user_id == current_user.id).first()

    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shopping cart is empty.")

    # Inventory check with pessimistic locking to prevent race conditions
    product_ids = [item.product_id for item in cart.items]
    db.query(models.Product).filter(models.Product.id.in_(product_ids)).with_for_update().all()

    # Check quantities after locking
    for item in cart.items:
        db.refresh(item.product)
        if item.product.quantity < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {item.product.name}. Available: {item.product.quantity}, Requested: {item.quantity}")

    total_price = sum(item.product.price * item.quantity for item in cart.items)

    # Create the main order record
    new_order = models.Order(
        user_id=current_user.id,
        total_price=total_price,
        status="pending"
    )
    db.add(new_order)
    db.flush()  # Get the new_order.id before committing

    # Create order items from cart items
    for item in cart.items:
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price  # Store the price at the time of purchase
        )
        db.add(order_item)

        # Decrement stock
        item.product.quantity -= item.quantity

    # Clear the cart by deleting its items
    db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete(synchronize_session=False)

    db.commit()
    db.refresh(new_order)

    # Eagerly load items for the response
    order_with_details = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.product)
    ).filter(models.Order.id == new_order.id).first()

    return order_with_details

@router.get("/", response_model=List[schemas.OrderListOut])
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Retrieve the current user's order history.
    """
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).order_by(models.Order.created_at.desc()).all()
    return orders

@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Retrieve the details of a specific order.
    Ensures the user can only access their own orders.
    """
    order: Optional[models.Order] = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.product)
    ).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this order.")

    return order

# Admin Endpoints

def check_admin(current_user: models.User = Depends(auth.get_current_user)):
    """Dependency to check if the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action."
        )

@router.get("/all/", response_model=List[schemas.OrderListOut], dependencies=[Depends(check_admin)])
def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db)
):
    """
    [Admin] Retrieve a list of all orders in the system with pagination.
    """
    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders

@router.patch("/{order_id}/status", response_model=schemas.OrderOut, dependencies=[Depends(check_admin)])
def update_order_status(
    order_id: int,
    order_update: schemas.OrderUpdate,
    db: Session = Depends(get_db)
):
    """
    [Admin] Update the status of a specific order.
    """
    order_query = db.query(models.Order).filter(models.Order.id == order_id)
    order: Optional[models.Order] = order_query.first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Update the status
    order_query.update({"status": order_update.status.value}, synchronize_session=False)
    db.commit()

    # Return the full, updated object with eager-loaded relations
    updated_order: Optional[models.Order] = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.product)
    ).filter(models.Order.id == order_id).first()

    return updated_order
