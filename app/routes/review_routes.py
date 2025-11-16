from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    tags=["Reviews"]
)

@router.post("/products/{product_id}/reviews", status_code=status.HTTP_201_CREATED, response_model=schemas.ReviewOut)
def create_review(
    product_id: int,
    review_data: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Create a new review for a product. A user can only review a product once.
    """
    if not (1 <= review_data.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")

    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    new_review = models.Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=review_data.rating,
        comment=review_data.comment
    )

    try:
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="You have already reviewed this product.")

    return new_review

@router.get("/products/{product_id}/reviews", response_model=List[schemas.ReviewOut])
def get_reviews_for_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get all reviews for a specific product.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    return product.reviews

@router.put("/reviews/{review_id}", response_model=schemas.ReviewOut)
def update_review(
    review_id: int,
    review_data: schemas.ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Update a review that you own.
    """
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action.")

    if not (1 <= review_data.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")

    review.rating = review_data.rating
    review.comment = review_data.comment
    db.commit()
    db.refresh(review)
    return review

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Delete a review. Can be deleted by the owner or an admin.
    """
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")

    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to perform this action.")

    db.delete(review)
    db.commit()
    return