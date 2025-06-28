from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.models.fun_zone import FunContent as FunContentModel, ContentType
from pydantic import BaseModel, Field

router = APIRouter()

class FunContentCreate(BaseModel):
    title: str
    content: str
    content_type: ContentType
    category: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False
    metadata: Optional[dict] = None

class FunContentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[ContentType] = Field(None, alias="type")
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    metadata: Optional[dict] = None

@router.post("/", response_model=FunContentModel, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_in: FunContentCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    content_dict = content_in.model_dump()
    
    # Map content_type to type for database
    if "content_type" in content_dict:
        content_dict["type"] = content_dict.pop("content_type")
    
    content_dict["user_id"] = str(current_user.id)
    content_dict["likes"] = 0
    content_dict["views"] = 0
    content_dict["comments_count"] = 0
    content_dict["created_at"] = datetime.now(timezone.utc)
    content_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.database.fun_content.insert_one(content_dict)
    content_dict["id"] = str(result.inserted_id)
    del content_dict["_id"]
    
    return FunContentModel(**content_dict)

@router.get("/", response_model=List[FunContentModel])
async def get_contents(
    content_type: Optional[ContentType] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    include_public: bool = Query(True),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Build query to get user's content and optionally public content
    query_conditions = [{"user_id": str(current_user.id)}]
    
    if include_public:
        query_conditions.append({"is_public": True})
    
    query = {"$or": query_conditions}
    
    if content_type:
        query["type"] = content_type
    if category:
        query["category"] = category
    if tag:
        query["tags"] = tag
    if is_public is not None:
        query["is_public"] = is_public
    
    contents = []
    async for content in db.database.fun_content.find(query).sort("created_at", -1):
        content["id"] = str(content["_id"])
        del content["_id"]
        # Ensure likes field exists
        if "likes" not in content:
            content["likes"] = 0
        contents.append(FunContentModel(**content))
    
    return contents

@router.get("/{content_id}", response_model=FunContentModel)
async def get_content(
    content_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    content = await db.database.fun_content.find_one({
        "_id": ObjectId(content_id),
        "$or": [
            {"user_id": str(current_user.id)},
            {"is_public": True}
        ]
    })
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Increment view count
    await db.database.fun_content.update_one(
        {"_id": ObjectId(content_id)},
        {"$inc": {"views": 1}}
    )
    
    content["id"] = str(content["_id"])
    del content["_id"]
    content["views"] += 1
    # Ensure likes field exists
    if "likes" not in content:
        content["likes"] = 0
    
    return FunContentModel(**content)

@router.put("/{content_id}", response_model=FunContentModel)
async def update_content(
    content_id: str,
    content_update: FunContentUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = content_update.model_dump(exclude_unset=True)
    
    # Map content_type to type for database
    if "content_type" in update_data:
        update_data["type"] = update_data.pop("content_type")
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await db.database.fun_content.update_one(
            {"_id": ObjectId(content_id), "user_id": str(current_user.id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or you don't have permission"
            )
    
    content = await db.database.fun_content.find_one({"_id": ObjectId(content_id)})
    content["id"] = str(content["_id"])
    del content["_id"]
    
    return FunContentModel(**content)

@router.post("/{content_id}/like", response_model=dict)
async def like_content(
    content_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if content exists and is public or owned by user
    content = await db.database.fun_content.find_one({
        "_id": ObjectId(content_id),
        "$or": [
            {"user_id": str(current_user.id)},
            {"is_public": True}
        ]
    })
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Check if user already liked this content
    like_key = f"like_{str(current_user.id)}_{content_id}"
    existing_like = await db.database.fun_likes.find_one({"_id": like_key})
    
    if existing_like:
        # Unlike
        await db.database.fun_likes.delete_one({"_id": like_key})
        await db.database.fun_content.update_one(
            {"_id": ObjectId(content_id)},
            {"$inc": {"likes": -1}}
        )
        return {"liked": False, "likes": content.get("likes", 1) - 1}
    else:
        # Like
        await db.database.fun_likes.insert_one({
            "_id": like_key,
            "user_id": str(current_user.id),
            "content_id": content_id,
            "created_at": datetime.now(timezone.utc)
        })
        await db.database.fun_content.update_one(
            {"_id": ObjectId(content_id)},
            {"$inc": {"likes": 1}}
        )
        return {"liked": True, "likes": content.get("likes", 0) + 1}

@router.get("/popular/week", response_model=List[FunContentModel])
async def get_popular_content(
    limit: int = Query(10, ge=1, le=50),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Get content from the last 7 days
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    pipeline = [
        {
            "$match": {
                "is_public": True,
                "created_at": {"$gte": week_ago}
            }
        },
        {
            "$addFields": {
                "popularity_score": {
                    "$add": [
                        {"$multiply": ["$likes", 2]},
                        "$views"
                    ]
                }
            }
        },
        {"$sort": {"popularity_score": -1}},
        {"$limit": limit}
    ]
    
    contents = []
    async for content in db.database.fun_content.aggregate(pipeline):
        content["id"] = str(content["_id"])
        del content["_id"]
        # Ensure likes field exists
        if "likes" not in content:
            content["likes"] = 0
        contents.append(FunContentModel(**content))
    
    return contents

@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    result = await db.database.fun_content.delete_one({
        "_id": ObjectId(content_id),
        "user_id": str(current_user.id)
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or you don't have permission"
        )
    
    # Also delete associated likes
    await db.database.fun_likes.delete_many({"content_id": content_id})