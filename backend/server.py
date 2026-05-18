from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import logging
from pathlib import Path
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Address(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    is_default: bool = False

class Product(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    price: float
    original_price: Optional[float] = None
    image_base64: Optional[str] = None
    stock: int
    category: str = "coffee"
    is_bestseller: bool = False
    is_new: bool = False
    tags: List[str] = []
    rating: float = 4.9
    reviews_count: int = 0

class CartItem(BaseModel):
    product_id: str
    quantity: int

class Cart(BaseModel):
    user_id: str
    items: List[CartItem] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    price: float
    quantity: int
    image_base64: Optional[str] = None

class Order(BaseModel):
    id: Optional[str] = None
    user_id: str
    items: List[OrderItem]
    total_amount: float
    shipping_address: Address
    payment_status: str = "pending"  # pending, completed, failed
    order_status: str = "processing"  # processing, shipped, delivered, cancelled
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Review(BaseModel):
    id: Optional[str] = None
    product_id: str
    user_id: str
    user_name: str
    rating: int  # 1-5
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewCreate(BaseModel):
    product_id: str
    rating: int
    comment: str

class Wishlist(BaseModel):
    user_id: str
    product_ids: List[str] = []

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ==================== AUTH UTILITIES ====================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_dict = {
        "name": user_data.name,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "phone": user_data.phone,
        "addresses": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_dict)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    # Initialize cart and wishlist
    await db.carts.insert_one({"user_id": user_id, "items": [], "updated_at": datetime.utcnow()})
    await db.wishlists.insert_one({"user_id": user_id, "product_ids": []})
    
    user_response = UserResponse(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        created_at=user_dict["created_at"]
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user_response)

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_id = str(user["_id"])
    access_token = create_access_token(data={"sub": user_id})
    
    user_response = UserResponse(
        id=user_id,
        name=user["name"],
        email=user["email"],
        phone=user.get("phone"),
        created_at=user["created_at"]
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user_response)

@api_router.get("/auth/profile", response_model=UserResponse)
async def get_profile(current_user = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        name=current_user["name"],
        email=current_user["email"],
        phone=current_user.get("phone"),
        created_at=current_user["created_at"]
    )

@api_router.put("/auth/profile")
async def update_profile(name: Optional[str] = None, phone: Optional[str] = None, current_user = Depends(get_current_user)):
    update_data = {}
    if name:
        update_data["name"] = name
    if phone:
        update_data["phone"] = phone
    
    if update_data:
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    
    return {"message": "Profile updated successfully"}

@api_router.post("/auth/addresses")
async def add_address(address: Address, current_user = Depends(get_current_user)):
    # If this is set as default, unset others
    if address.is_default:
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {"addresses.$[].is_default": False}}
        )
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$push": {"addresses": address.dict()}}
    )
    
    return {"message": "Address added successfully"}

@api_router.get("/auth/addresses")
async def get_addresses(current_user = Depends(get_current_user)):
    user = await db.users.find_one({"_id": current_user["_id"]})
    return user.get("addresses", [])

# ==================== PRODUCTS ENDPOINTS ====================

@api_router.get("/products", response_model=List[Product])
async def get_products(category: Optional[str] = None, is_bestseller: Optional[bool] = None):
    query = {}
    if category:
        query["category"] = category
    if is_bestseller is not None:
        query["is_bestseller"] = is_bestseller
    
    products = await db.products.find(query).to_list(100)
    return [Product(id=str(p["_id"]), **{k: v for k, v in p.items() if k != "_id"}) for p in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return Product(id=str(product["_id"]), **{k: v for k, v in product.items() if k != "_id"})

@api_router.post("/products")
async def create_product(product: Product):
    product_dict = product.dict(exclude={"id"})
    result = await db.products.insert_one(product_dict)
    return {"id": str(result.inserted_id), "message": "Product created successfully"}

# ==================== CART ENDPOINTS ====================

@api_router.get("/cart")
async def get_cart(current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    cart = await db.carts.find_one({"user_id": user_id})
    
    if not cart or not cart.get("items"):
        return {"items": [], "total": 0}
    
    # Fetch product details for each item
    cart_items = []
    total = 0
    
    for item in cart["items"]:
        product = await db.products.find_one({"_id": ObjectId(item["product_id"])})
        if product:
            cart_items.append({
                "product_id": str(product["_id"]),
                "name": product["name"],
                "price": product["price"],
                "image_base64": product.get("image_base64"),
                "quantity": item["quantity"],
                "stock": product["stock"]
            })
            total += product["price"] * item["quantity"]
    
    return {"items": cart_items, "total": total}

@api_router.post("/cart/add")
async def add_to_cart(product_id: str, quantity: int = 1, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Check if product exists and has stock
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product["stock"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    cart = await db.carts.find_one({"user_id": user_id})
    
    if not cart:
        await db.carts.insert_one({"user_id": user_id, "items": [{"product_id": product_id, "quantity": quantity}], "updated_at": datetime.utcnow()})
    else:
        # Check if item already in cart
        item_exists = False
        for item in cart.get("items", []):
            if item["product_id"] == product_id:
                item_exists = True
                new_quantity = item["quantity"] + quantity
                if new_quantity > product["stock"]:
                    raise HTTPException(status_code=400, detail="Insufficient stock")
                await db.carts.update_one(
                    {"user_id": user_id, "items.product_id": product_id},
                    {"$set": {"items.$.quantity": new_quantity, "updated_at": datetime.utcnow()}}
                )
                break
        
        if not item_exists:
            await db.carts.update_one(
                {"user_id": user_id},
                {"$push": {"items": {"product_id": product_id, "quantity": quantity}}, "$set": {"updated_at": datetime.utcnow()}}
            )
    
    return {"message": "Item added to cart"}

@api_router.put("/cart/update")
async def update_cart_item(product_id: str, quantity: int, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    if quantity <= 0:
        # Remove item
        await db.carts.update_one(
            {"user_id": user_id},
            {"$pull": {"items": {"product_id": product_id}}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return {"message": "Item removed from cart"}
    
    # Check stock
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product["stock"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    await db.carts.update_one(
        {"user_id": user_id, "items.product_id": product_id},
        {"$set": {"items.$.quantity": quantity, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Cart updated"}

@api_router.delete("/cart/remove/{product_id}")
async def remove_from_cart(product_id: str, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    await db.carts.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}, "$set": {"updated_at": datetime.utcnow()}}
    )
    return {"message": "Item removed from cart"}

@api_router.delete("/cart/clear")
async def clear_cart(current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "updated_at": datetime.utcnow()}}
    )
    return {"message": "Cart cleared"}

# ==================== ORDERS ENDPOINTS ====================

@api_router.post("/orders")
async def create_order(order: Order, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    order.user_id = user_id
    
    # Verify stock and calculate total
    total = 0
    for item in order.items:
        product = await db.products.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product["stock"] < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product['name']}")
        total += product["price"] * item.quantity
    
    order.total_amount = total
    order_dict = order.dict(exclude={"id"})
    result = await db.orders.insert_one(order_dict)
    
    # Clear cart after order
    await db.carts.update_one({"user_id": user_id}, {"$set": {"items": [], "updated_at": datetime.utcnow()}})
    
    # Reduce stock
    for item in order.items:
        await db.products.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"stock": -item.quantity}}
        )
    
    return {"id": str(result.inserted_id), "message": "Order created successfully"}

@api_router.get("/orders")
async def get_orders(current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    orders = await db.orders.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    
    return [
        {
            "id": str(order["_id"]),
            **{k: v for k, v in order.items() if k != "_id"}
        }
        for order in orders
    ]

@api_router.get("/orders/{order_id}")
async def get_order(order_id: str, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")
    
    order = await db.orders.find_one({"_id": ObjectId(order_id), "user_id": user_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": str(order["_id"]),
        **{k: v for k, v in order.items() if k != "_id"}
    }

@api_router.put("/orders/{order_id}/payment")
async def update_payment_status(order_id: str, payment_status: str, razorpay_payment_id: Optional[str] = None, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    update_data = {"payment_status": payment_status}
    if razorpay_payment_id:
        update_data["razorpay_payment_id"] = razorpay_payment_id
    
    if payment_status == "completed":
        update_data["order_status"] = "confirmed"
    
    await db.orders.update_one(
        {"_id": ObjectId(order_id), "user_id": user_id},
        {"$set": update_data}
    )
    
    return {"message": "Payment status updated"}

# ==================== REVIEWS ENDPOINTS ====================

@api_router.get("/reviews/{product_id}")
async def get_reviews(product_id: str):
    reviews = await db.reviews.find({"product_id": product_id}).sort("created_at", -1).to_list(100)
    return [
        {
            "id": str(review["_id"]),
            **{k: v for k, v in review.items() if k != "_id"}
        }
        for review in reviews
    ]

@api_router.post("/reviews")
async def create_review(review_data: ReviewCreate, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Check if user has ordered this product
    order = await db.orders.find_one({
        "user_id": user_id,
        "items.product_id": review_data.product_id,
        "order_status": {"$in": ["delivered", "confirmed"]}
    })
    
    if not order:
        raise HTTPException(status_code=400, detail="You can only review products you've ordered")
    
    review_dict = {
        "product_id": review_data.product_id,
        "user_id": user_id,
        "user_name": current_user["name"],
        "rating": review_data.rating,
        "comment": review_data.comment,
        "created_at": datetime.utcnow()
    }
    
    result = await db.reviews.insert_one(review_dict)
    
    # Update product rating
    reviews = await db.reviews.find({"product_id": review_data.product_id}).to_list(1000)
    avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    await db.products.update_one(
        {"_id": ObjectId(review_data.product_id)},
        {"$set": {"rating": round(avg_rating, 1), "reviews_count": len(reviews)}}
    )
    
    return {"id": str(result.inserted_id), "message": "Review added successfully"}

# ==================== WISHLIST ENDPOINTS ====================

@api_router.get("/wishlist")
async def get_wishlist(current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    wishlist = await db.wishlists.find_one({"user_id": user_id})
    
    if not wishlist or not wishlist.get("product_ids"):
        return []
    
    # Fetch product details
    products = []
    for product_id in wishlist["product_ids"]:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
        if product:
            products.append(Product(id=str(product["_id"]), **{k: v for k, v in product.items() if k != "_id"}))
    
    return products

@api_router.post("/wishlist/add/{product_id}")
async def add_to_wishlist(product_id: str, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Check if product exists
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.wishlists.update_one(
        {"user_id": user_id},
        {"$addToSet": {"product_ids": product_id}},
        upsert=True
    )
    
    return {"message": "Added to wishlist"}

@api_router.delete("/wishlist/remove/{product_id}")
async def remove_from_wishlist(product_id: str, current_user = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    await db.wishlists.update_one(
        {"user_id": user_id},
        {"$pull": {"product_ids": product_id}}
    )
    
    return {"message": "Removed from wishlist"}

# ==================== CONTACT ENDPOINT ====================

@api_router.post("/contact")
async def submit_contact_form(form: ContactForm):
    await db.contacts.insert_one(form.dict())
    return {"message": "Thank you for contacting us! We'll get back to you soon."}

# ==================== SEED DATA ====================

@api_router.post("/seed")
async def seed_database():
    # Clear existing data
    await db.products.delete_many({})
    
    # Sample products
    products = [
        {
            "name": "Demo Pack",
            "description": "A bold, aromatic, caffeine-free roast — perfect for your daily ritual. Free test sample to try Dazeen.",
            "price": 0,
            "original_price": 0,
            "image_base64": None,
            "stock": 999,
            "category": "coffee",
            "is_bestseller": False,
            "is_new": True,
            "tags": ["Free Test", "Demo"],
            "rating": 4.9,
            "reviews_count": 0
        },
        {
            "name": "Dazeen Date Seed Coffee - 100g",
            "description": "A bold, aromatic, caffeine-free roast — perfect for your daily ritual. Handcrafted from premium date seeds, 100% natural and caffeine-free.",
            "price": 349,
            "original_price": 449,
            "image_base64": None,
            "stock": 100,
            "category": "coffee",
            "is_bestseller": True,
            "is_new": False,
            "tags": ["Bestseller", "100g Pack"],
            "rating": 4.9,
            "reviews_count": 1240
        },
        {
            "name": "Dazeen Date Seed Coffee - 250g",
            "description": "A bold, aromatic, caffeine-free roast — perfect for your daily ritual. Best value pack with premium date seeds.",
            "price": 749,
            "original_price": 999,
            "image_base64": None,
            "stock": 50,
            "category": "coffee",
            "is_bestseller": True,
            "is_new": False,
            "tags": ["Best Value", "250g Pack"],
            "rating": 4.9,
            "reviews_count": 1160
        }
    ]
    
    await db.products.insert_many(products)
    
    return {"message": "Database seeded successfully"}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
