from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import asyncio

from models import (
    User, UserCreate, UserLogin, Token, UserRole,
    Lead, LeadCreate, LeadStatus,
    Bid, BidCreate,
    PhotoUploadResponse, DamageAssessment
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role, require_any_role
)
from database import db, create_indexes, close_db_connection
from mock_services import (
    ai_service, ocr_service, sms_service,
    payment_service, storage_service
)

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Claim2Car Connect API",
    description="AI-Powered Total-Loss Vehicle Acquisition Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
api = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, lead_id: str, websocket: WebSocket):
        await websocket.accept()
        if lead_id not in self.active_connections:
            self.active_connections[lead_id] = []
        self.active_connections[lead_id].append(websocket)
        logger.info(f"WebSocket connected for lead {lead_id}")
    
    def disconnect(self, lead_id: str, websocket: WebSocket):
        if lead_id in self.active_connections:
            self.active_connections[lead_id].remove(websocket)
            if not self.active_connections[lead_id]:
                del self.active_connections[lead_id]
        logger.info(f"WebSocket disconnected for lead {lead_id}")
    
    async def broadcast(self, lead_id: str, message: dict):
        if lead_id in self.active_connections:
            for connection in self.active_connections[lead_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")

manager = ConnectionManager()

# In-memory bid storage (simulating Redis)
active_bids: Dict[str, List[Dict]] = {}
bid_timers: Dict[str, datetime] = {}


# ==================== AUTH ENDPOINTS ====================

@api.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_dict = user_data.model_dump()
    user_dict["hashed_password"] = hash_password(user_data.password)
    del user_dict["password"]
    
    user = User(**user_dict)
    user_doc = user.model_dump()
    user_doc["created_at"] = user_doc["created_at"].isoformat()
    user_doc["updated_at"] = user_doc["updated_at"].isoformat()
    
    await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "full_name": user.full_name
    })
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    )


@api.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login a user."""
    # Find user
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token({
        "sub": user_doc["id"],
        "email": user_doc["email"],
        "role": user_doc["role"],
        "full_name": user_doc["full_name"]
    })
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user_doc["id"],
            "email": user_doc["email"],
            "full_name": user_doc["full_name"],
            "role": user_doc["role"]
        }
    )


@api.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    user_doc = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "hashed_password": 0})
    return user_doc


# ==================== PHOTO UPLOAD ENDPOINTS ====================

@api.post("/photos/presigned-url", response_model=PhotoUploadResponse)
async def get_presigned_url(
    filename: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Get presigned URL for photo upload."""
    result = storage_service.generate_presigned_upload_url(filename)
    return PhotoUploadResponse(**result)


# ==================== LEAD ENDPOINTS ====================

@api.post("/leads", status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    current_user: dict = Depends(require_role(UserRole.TOW_OPERATOR))
):
    """Create a new lead (Tow Operator only)."""
    # Run AI damage detection
    if lead_data.photos:
        damage_assessment_data = ai_service.detect_damage(lead_data.photos)
        damage_assessment = DamageAssessment(**damage_assessment_data)
    else:
        damage_assessment = None
    
    # Create lead
    lead = Lead(
        tow_operator_id=current_user["id"],
        vehicle_info=lead_data.vehicle_info,
        location=lead_data.location,
        contact_info=lead_data.contact_info,
        photos=lead_data.photos,
        damage_assessment=damage_assessment,
        status=LeadStatus.PENDING
    )
    
    lead_doc = lead.model_dump()
    lead_doc["created_at"] = lead_doc["created_at"].isoformat()
    lead_doc["updated_at"] = lead_doc["updated_at"].isoformat()
    
    await db.leads.insert_one(lead_doc)
    
    # Send SMS to owner if AI detected total loss
    if damage_assessment and damage_assessment.total_loss_probability >= 85:
        sms_message = (
            f"Sorry about your crash 😔\n"
            f"Get instant cash offers for your vehicle!\n"
            f"Tap here to see offers: https://claim2car.com/owner/{lead.id}"
        )
        sms_service.send_sms(lead_data.contact_info.phone, sms_message)
        
        # Update status to available
        await db.leads.update_one(
            {"id": lead.id},
            {"$set": {"status": LeadStatus.AVAILABLE.value}}
        )
    
    logger.info(f"Lead created: {lead.id} by tow operator {current_user['id']}")
    
    return {
        "id": lead.id,
        "status": lead.status.value,
        "damage_assessment": damage_assessment.model_dump() if damage_assessment else None,
        "message": "Lead created successfully"
    }


@api.get("/leads")
async def get_leads(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get leads based on user role."""
    query = {}
    
    # Filter by role
    if current_user["role"] == UserRole.TOW_OPERATOR.value:
        query["tow_operator_id"] = current_user["id"]
    elif current_user["role"] == UserRole.DEALER.value:
        if not status:
            query["status"] = {"$in": [LeadStatus.AVAILABLE.value, LeadStatus.BIDDING.value]}
    elif current_user["role"] == UserRole.OWNER.value:
        query["contact_info.email"] = current_user["email"]
    
    # Filter by status if provided
    if status:
        query["status"] = status
    
    leads = await db.leads.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return leads


@api.get("/leads/{lead_id}")
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific lead."""
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Get bids for this lead
    bids = await db.bids.find({"lead_id": lead_id}, {"_id": 0}).sort("bid_amount", -1).to_list(100)
    lead["bids"] = bids
    
    return lead


@api.post("/leads/{lead_id}/opt-in")
async def owner_opt_in(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Owner opts in to receive bids."""
    lead = await db.leads.find_one({"id": lead_id})
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Update lead status
    await db.leads.update_one(
        {"id": lead_id},
        {
            "$set": {
                "owner_opted_in": True,
                "owner_opt_in_at": datetime.utcnow().isoformat(),
                "status": LeadStatus.AVAILABLE.value
            }
        }
    )
    
    return {"message": "Successfully opted in", "lead_id": lead_id}


# ==================== BID ENDPOINTS ====================

@api.post("/bids", status_code=status.HTTP_201_CREATED)
async def create_bid(
    bid_data: BidCreate,
    current_user: dict = Depends(require_role(UserRole.DEALER))
):
    """Create a new bid (Dealer only)."""
    # Check if lead exists and is available
    lead = await db.leads.find_one({"id": bid_data.lead_id})
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    if lead["status"] not in [LeadStatus.AVAILABLE.value, LeadStatus.BIDDING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead is not available for bidding"
        )
    
    # Create bid
    bid = Bid(
        lead_id=bid_data.lead_id,
        dealer_id=current_user["id"],
        dealer_name=current_user["full_name"],
        bid_amount=bid_data.bid_amount,
        expires_at=datetime.utcnow() + timedelta(minutes=3)
    )
    
    bid_doc = bid.model_dump()
    bid_doc["created_at"] = bid_doc["created_at"].isoformat()
    if bid_doc.get("expires_at"):
        bid_doc["expires_at"] = bid_doc["expires_at"].isoformat()
    
    await db.bids.insert_one(bid_doc)
    
    # Update lead status to bidding
    await db.leads.update_one(
        {"id": bid_data.lead_id},
        {"$set": {"status": LeadStatus.BIDDING.value}}
    )
    
    # Store bid in active bids
    if bid_data.lead_id not in active_bids:
        active_bids[bid_data.lead_id] = []
        bid_timers[bid_data.lead_id] = datetime.utcnow() + timedelta(minutes=3)
    
    active_bids[bid_data.lead_id].append(bid_doc)
    
    # Broadcast new bid via WebSocket
    await manager.broadcast(bid_data.lead_id, {
        "type": "NEW_BID",
        "bid": bid_doc,
        "time_remaining": 180
    })
    
    logger.info(f"Bid created: ${bid.bid_amount} by dealer {current_user['id']} for lead {bid_data.lead_id}")
    
    return {"id": bid.id, "message": "Bid placed successfully"}


@api.get("/bids/lead/{lead_id}")
async def get_lead_bids(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all bids for a lead."""
    bids = await db.bids.find({"lead_id": lead_id}, {"_id": 0}).sort("bid_amount", -1).to_list(100)
    return bids


@api.post("/bids/{bid_id}/accept")
async def accept_bid(
    bid_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Accept a bid (Owner only)."""
    # Get bid
    bid = await db.bids.find_one({"id": bid_id})
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid not found"
        )
    
    # Update bid status
    await db.bids.update_one(
        {"id": bid_id},
        {"$set": {"status": "accepted"}}
    )
    
    # Update lead
    await db.leads.update_one(
        {"id": bid["lead_id"]},
        {
            "$set": {
                "status": LeadStatus.CLAIMED.value,
                "claimed_by": bid["dealer_id"],
                "final_bid_amount": bid["bid_amount"],
                "claimed_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    # Create mock payment
    payment_service.create_payment_intent(
        amount=bid["bid_amount"],
        dealer_id=bid["dealer_id"],
        lead_id=bid["lead_id"]
    )
    
    # Broadcast acceptance
    await manager.broadcast(bid["lead_id"], {
        "type": "BID_ACCEPTED",
        "bid_id": bid_id,
        "dealer_id": bid["dealer_id"],
        "amount": bid["bid_amount"]
    })
    
    logger.info(f"Bid accepted: {bid_id} for lead {bid['lead_id']}")
    
    return {"message": "Bid accepted successfully"}


# ==================== WEBSOCKET ENDPOINT ====================

@app.websocket("/ws/leads/{lead_id}")
async def websocket_endpoint(websocket: WebSocket, lead_id: str):
    """WebSocket endpoint for real-time bid updates."""
    await manager.connect(lead_id, websocket)
    
    try:
        # Send initial bids
        bids = await db.bids.find({"lead_id": lead_id}, {"_id": 0}).sort("bid_amount", -1).to_list(100)
        await websocket.send_json({
            "type": "INITIAL_BIDS",
            "bids": bids
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back or handle client messages
            await websocket.send_json({"type": "PONG", "message": "Connected"})
    
    except WebSocketDisconnect:
        manager.disconnect(lead_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(lead_id, websocket)


# ==================== HEALTH CHECK ====================

@api.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Claim2Car Connect API",
        "version": "1.0.0"
    }


# Include router
app.include_router(api)


# ==================== STARTUP/SHUTDOWN EVENTS ====================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Claim2Car Connect API...")
    await create_indexes()
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Claim2Car Connect API...")
    await close_db_connection()
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
