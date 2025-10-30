from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.getenv('DB_NAME', 'claim2car_db')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


async def get_db():
    """Dependency to get database instance."""
    return db


async def create_indexes():
    """Create database indexes for better performance."""
    try:
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("role")
        await db.users.create_index("created_at")
        
        # Leads collection indexes
        await db.leads.create_index("tow_operator_id")
        await db.leads.create_index("status")
        await db.leads.create_index("claimed_by")
        await db.leads.create_index("created_at")
        await db.leads.create_index([("location.latitude", "2d"), ("location.longitude", "2d")])
        
        # Bids collection indexes
        await db.bids.create_index("lead_id")
        await db.bids.create_index("dealer_id")
        await db.bids.create_index("status")
        await db.bids.create_index("created_at")
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")


async def close_db_connection():
    """Close database connection."""
    client.close()
    logger.info("Database connection closed")
