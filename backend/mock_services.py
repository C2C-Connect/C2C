import os
import random
import string
import base64
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"


class MockAIService:
    """Mock AI damage detection service."""
    
    @staticmethod
    def detect_damage(photo_urls: List[str]) -> Dict[str, Any]:
        """Mock damage detection from photos."""
        logger.info(f"[MOCK AI] Analyzing {len(photo_urls)} photos for damage")
        
        # Simulate AI processing
        damage_types = [
            "Front bumper damage",
            "Hood dent",
            "Left door scratches",
            "Broken headlight",
            "Cracked windshield",
            "Rear panel damage"
        ]
        
        # Random damage assessment
        num_damages = random.randint(2, 5)
        selected_damages = random.sample(damage_types, num_damages)
        
        severity_score = random.randint(60, 95)
        estimated_repair_cost = random.randint(8000, 25000)
        
        # Total loss if repair > 75% of estimated value
        estimated_vehicle_value = random.randint(15000, 35000)
        repair_ratio = estimated_repair_cost / estimated_vehicle_value
        total_loss_probability = min(repair_ratio * 100, 95)
        
        structural_damage = severity_score > 75
        airbag_deployed = random.choice([True, False])
        
        if airbag_deployed:
            estimated_repair_cost += random.randint(2000, 5000)
        
        return {
            "total_loss_probability": round(total_loss_probability, 2),
            "estimated_repair_cost": estimated_repair_cost,
            "damage_categories": selected_damages,
            "severity_score": severity_score,
            "structural_damage": structural_damage,
            "airbag_deployed": airbag_deployed,
            "damage_description": f"Vehicle shows {', '.join(selected_damages).lower()}. "
                                 f"Severity rated at {severity_score}/100.",
            "estimated_vehicle_value": estimated_vehicle_value
        }


class MockOCRService:
    """Mock OCR service for document extraction."""
    
    @staticmethod
    def extract_license_plate(photo_url: str) -> str:
        """Mock license plate extraction."""
        logger.info(f"[MOCK OCR] Extracting license plate from {photo_url}")
        
        # Generate random license plate
        state = random.choice(["TX", "CA", "FL", "NY", "GA"])
        numbers = ''.join(random.choices(string.digits, k=3))
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        return f"{state}-{letters}{numbers}"
    
    @staticmethod
    def extract_vin(photo_url: str) -> str:
        """Mock VIN extraction."""
        logger.info(f"[MOCK OCR] Extracting VIN from {photo_url}")
        
        # Generate random VIN (17 characters)
        vin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
        return vin.replace('O', '0').replace('I', '1').replace('Q', '0')
    
    @staticmethod
    def extract_driver_license(photo_url: str) -> Dict[str, Any]:
        """Mock driver's license extraction."""
        logger.info(f"[MOCK OCR] Extracting driver's license info from {photo_url}")
        
        return {
            "name": f"{random.choice(['John', 'Jane', 'Mike', 'Sarah'])} "
                   f"{random.choice(['Smith', 'Johnson', 'Williams', 'Brown'])}",
            "license_number": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            "state": random.choice(["TX", "CA", "FL", "NY", "GA"]),
            "expiration_date": (datetime.now() + timedelta(days=365*2)).strftime("%Y-%m-%d"),
            "confidence": round(random.uniform(0.85, 0.98), 2)
        }


class MockSMSService:
    """Mock SMS notification service (Twilio)."""
    
    def __init__(self):
        self.messages_sent = []
    
    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Mock SMS sending."""
        logger.info(f"[MOCK SMS] Sending to {to_phone}: {message}")
        
        mock_message_id = 'SM' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        
        self.messages_sent.append({
            "to": to_phone,
            "message": message,
            "message_id": mock_message_id,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat()
        })
        
        return {
            "message_id": mock_message_id,
            "status": "sent",
            "to": to_phone
        }


class MockPaymentService:
    """Mock payment processing service (Stripe)."""
    
    def __init__(self):
        self.payments = []
        self.accounts = {}
    
    def create_payment_intent(self, amount: float, dealer_id: str, lead_id: str) -> Dict[str, Any]:
        """Mock payment intent creation."""
        logger.info(f"[MOCK PAYMENT] Creating payment intent for ${amount} - Dealer: {dealer_id}")
        
        payment_intent_id = 'pi_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))
        
        payment = {
            "payment_intent_id": payment_intent_id,
            "amount": amount,
            "dealer_id": dealer_id,
            "lead_id": lead_id,
            "status": "requires_capture",
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.payments.append(payment)
        
        return payment
    
    def capture_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Mock payment capture."""
        logger.info(f"[MOCK PAYMENT] Capturing payment {payment_intent_id}")
        
        for payment in self.payments:
            if payment["payment_intent_id"] == payment_intent_id:
                payment["status"] = "succeeded"
                payment["captured_at"] = datetime.utcnow().isoformat()
                return payment
        
        return {"error": "Payment intent not found"}
    
    def create_payout(self, amount: float, recipient_id: str, description: str) -> Dict[str, Any]:
        """Mock payout creation."""
        logger.info(f"[MOCK PAYMENT] Creating payout of ${amount} to {recipient_id}")
        
        payout_id = 'po_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))
        
        return {
            "payout_id": payout_id,
            "amount": amount,
            "recipient_id": recipient_id,
            "description": description,
            "status": "paid",
            "created_at": datetime.utcnow().isoformat()
        }


class MockStorageService:
    """Mock file storage service (AWS S3)."""
    
    def __init__(self):
        self.files = {}
    
    def generate_presigned_upload_url(self, filename: str) -> Dict[str, str]:
        """Mock presigned URL generation."""
        logger.info(f"[MOCK S3] Generating presigned URL for {filename}")
        
        file_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        mock_url = f"https://mock-storage.claim2car.com/uploads/{file_id}/{filename}"
        
        return {
            "upload_url": mock_url,
            "photo_url": mock_url,
            "filename": filename
        }
    
    def store_file(self, filename: str, content: bytes) -> str:
        """Mock file storage."""
        logger.info(f"[MOCK S3] Storing file {filename} ({len(content)} bytes)")
        
        file_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        file_url = f"https://mock-storage.claim2car.com/uploads/{file_id}/{filename}"
        
        self.files[file_id] = {
            "filename": filename,
            "url": file_url,
            "size": len(content),
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        return file_url


# Global instances
ai_service = MockAIService()
ocr_service = MockOCRService()
sms_service = MockSMSService()
payment_service = MockPaymentService()
storage_service = MockStorageService()
