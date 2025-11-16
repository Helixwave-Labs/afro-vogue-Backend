from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    profile_picture_url: Optional[str] = None
    id: int
    username: str
    email: EmailStr
    is_active: bool
    role: str
    created_at: datetime

    class Config:
      from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class EmailVerification(BaseModel):
    email: EmailStr
    otp: str

class ResendOTPRequest(BaseModel):
    email: EmailStr

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# Schemas for Categories and SubCategories
class SubCategoryBase(BaseModel):
    name: str

class SubCategoryCreate(SubCategoryBase):
    pass

class SubCategoryOut(SubCategoryBase):
    id: int
    category_id: int
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    subcategories: list[SubCategoryOut] = []
    class Config:
        from_attributes = True

# Schemas for Products
class ProductBase(BaseModel):
    name: str
    description: str
    price: float

class ProductCreate(ProductBase):
    subcategory_id: int
    quantity: int

# Schemas for Reviews
class ReviewBase(BaseModel):
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(ReviewBase):
    pass

class ReviewOut(ReviewBase):
    id: int
    user: UserOut
    created_at: datetime
    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    subcategory_id: Optional[int] = None
    quantity: Optional[int] = None

class ProductOut(ProductBase):
    id: int
    image_url: Optional[str] = None
    owner_id: int
    quantity: int
    owner: UserOut # Nested schema to show owner details
    subcategory: SubCategoryOut
    reviews: list[ReviewOut] = []
    average_rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True

# Schemas for Shopping Cart
class CartItemAdd(BaseModel):
    product_id: int
    quantity: int

class CartProductOut(BaseModel):
    """A simplified product schema for cart items."""
    id: int
    name: str
    price: float
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class CartItemOut(BaseModel):
    quantity: int
    product: CartProductOut

    class Config:
        from_attributes = True

class CartOut(BaseModel):
    items: list[CartItemOut]
    total_price: float
    total_items: int

# Schemas for Orders
class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderUpdate(BaseModel):
    status: OrderStatus


class OrderItemOut(BaseModel):
    quantity: int
    price: float # Price per item at time of purchase
    product: Optional[CartProductOut] # Product can be null if it's deleted later

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    status: OrderStatus
    total_price: float
    created_at: datetime
    items: list[OrderItemOut]

    class Config:
        from_attributes = True

class OrderListOut(BaseModel):
    id: int
    status: OrderStatus
    total_price: float
    created_at: datetime

# Schema for Wishlist
class WishlistOut(BaseModel):
    products: list[CartProductOut] # Reusing CartProductOut for a consistent product representation
