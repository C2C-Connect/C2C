from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class UserRole(str, Enum):
    ADMIN = "admin"
    TOW_OPERATOR = "tow_operator"
    DEALER = "dealer"
    OWNER = "owner"


class LeadStatus(str, Enum):
    PENDING = "pending"
    AVAILABLE = "available"
    BIDDING = "bidding"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    EXPIRED = "expired"


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashed_password: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    company_name: Optional[str] = None
    license_number: Optional[str] = None  # For tow operators
    dealer_license: Optional[str] = None  # For dealers
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    stripe_account_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    company_name: Optional[str] = None
    license_number: Optional[str] = None
    dealer_license: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]


class Location(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    zip_code: str


class VehicleInfo(BaseModel):
    vin: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    estimated_value: Optional[float] = None


class DamageAssessment(BaseModel):
    total_loss_probability: float
    estimated_repair_cost: float
    damage_categories: List[str]
    severity_score: int  # 0-100
    structural_damage: bool
    airbag_deployed: bool
    damage_description: str


class ContactInfo(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None


class Lead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tow_operator_id: str
    vehicle_info: VehicleInfo
    location: Location
    contact_info: ContactInfo
    damage_assessment: Optional[DamageAssessment] = None
    photos: List[str] = []  # URLs to photos
    status: LeadStatus = LeadStatus.PENDING
    owner_opted_in: bool = False
    owner_opt_in_at: Optional[datetime] = None
    claimed_by: Optional[str] = None  # Dealer ID
    final_bid_amount: Optional[float] = None
    claimed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LeadCreate(BaseModel):
    vehicle_info: VehicleInfo
    location: Location
    contact_info: ContactInfo
    photos: List[str] = []


class Bid(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    dealer_id: str
    dealer_name: str
    bid_amount: float
    status: str = "active"  # active, accepted, rejected, expired
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class BidCreate(BaseModel):
    lead_id: str
    bid_amount: float


class PhotoUpload(BaseModel):
    filename: str
    content_type: str


class PhotoUploadResponse(BaseModel):
    upload_url: str
    photo_url: str
    filename: str
