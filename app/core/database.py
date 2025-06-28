from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import certifi

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_database():
    # Check if using MongoDB Atlas (contains mongodb+srv or mongodb.net)
    if "mongodb+srv" in settings.MONGODB_URL or "mongodb.net" in settings.MONGODB_URL:
        # MongoDB Atlas requires SSL/TLS certificate verification
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True,
            w='majority'
        )
    else:
        # Local MongoDB doesn't need SSL
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
    
    db.database = db.client[settings.DATABASE_NAME]
    print(f"Connected to MongoDB at {settings.MONGODB_URL}")

async def close_database_connection():
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")