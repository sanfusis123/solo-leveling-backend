from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.models.learning_material import (
    LearningMaterial as LearningMaterialModel,
    MaterialType,
    VisibilityLevel
)
from pydantic import BaseModel

router = APIRouter()

class LearningMaterialCreate(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    type: MaterialType = MaterialType.NOTE
    subject: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    visibility: VisibilityLevel = VisibilityLevel.PRIVATE
    references: List[str] = []

class LearningMaterialUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    type: Optional[MaterialType] = None
    subject: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[VisibilityLevel] = None
    references: Optional[List[str]] = None

class ShareMaterial(BaseModel):
    user_ids: List[str]

@router.post("/", response_model=LearningMaterialModel, status_code=status.HTTP_201_CREATED)
async def create_material(
    material_in: LearningMaterialCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    material_dict = material_in.model_dump()
    material_dict["user_id"] = str(current_user.id)
    material_dict["shared_with"] = []
    material_dict["attachments"] = []
    material_dict["view_count"] = 0
    material_dict["like_count"] = 0
    material_dict["is_archived"] = False
    material_dict["created_at"] = datetime.now(timezone.utc)
    material_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.database.learning_materials.insert_one(material_dict)
    material_dict["id"] = str(result.inserted_id)
    del material_dict["_id"]
    
    return LearningMaterialModel(**material_dict)

@router.get("/", response_model=List[LearningMaterialModel])
async def get_materials(
    type: Optional[MaterialType] = Query(None),
    subject: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_archived: Optional[bool] = Query(False),
    include_public: bool = Query(True),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Build query to get user's materials and optionally public materials
    query_conditions = [
        {"user_id": str(current_user.id)},
        {"shared_with": str(current_user.id)}
    ]
    
    if include_public:
        query_conditions.append({"visibility": VisibilityLevel.PUBLIC})
    
    query = {"$or": query_conditions}
    
    if type:
        query["type"] = type
    if subject:
        query["subject"] = subject
    if category:
        query["category"] = category
    if tag:
        query["tags"] = tag
    if is_archived is not None:
        query["is_archived"] = is_archived
    
    materials = []
    async for material in db.database.learning_materials.find(query).sort("created_at", -1):
        material["id"] = str(material["_id"])
        del material["_id"]
        materials.append(LearningMaterialModel(**material))
    
    return materials

@router.get("/{material_id}", response_model=LearningMaterialModel)
async def get_material(
    material_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    material = await db.database.learning_materials.find_one({
        "_id": ObjectId(material_id),
        "$or": [
            {"user_id": str(current_user.id)},
            {"shared_with": str(current_user.id)},
            {"visibility": VisibilityLevel.PUBLIC}
        ]
    })
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Increment view count
    await db.database.learning_materials.update_one(
        {"_id": ObjectId(material_id)},
        {"$inc": {"view_count": 1}}
    )
    
    material["id"] = str(material["_id"])
    del material["_id"]
    material["view_count"] += 1
    
    return LearningMaterialModel(**material)

@router.put("/{material_id}", response_model=LearningMaterialModel)
async def update_material(
    material_id: str,
    material_update: LearningMaterialUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = material_update.model_dump(exclude_unset=True)
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await db.database.learning_materials.update_one(
            {"_id": ObjectId(material_id), "user_id": str(current_user.id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found or you don't have permission"
            )
    
    material = await db.database.learning_materials.find_one({"_id": ObjectId(material_id)})
    material["id"] = str(material["_id"])
    del material["_id"]
    
    return LearningMaterialModel(**material)

@router.post("/{material_id}/share", response_model=LearningMaterialModel)
async def share_material(
    material_id: str,
    share_data: ShareMaterial,
    current_user: UserModel = Depends(get_current_active_user)
):
    # Verify ownership
    material = await db.database.learning_materials.find_one({
        "_id": ObjectId(material_id),
        "user_id": str(current_user.id)
    })
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or you don't have permission"
        )
    
    # Update shared_with list
    result = await db.database.learning_materials.update_one(
        {"_id": ObjectId(material_id)},
        {
            "$addToSet": {"shared_with": {"$each": share_data.user_ids}},
            "$set": {"visibility": VisibilityLevel.SHARED, "updated_at": datetime.now(timezone.utc)}
        }
    )
    
    material = await db.database.learning_materials.find_one({"_id": ObjectId(material_id)})
    material["id"] = str(material["_id"])
    del material["_id"]
    
    return LearningMaterialModel(**material)

@router.post("/{material_id}/archive", response_model=LearningMaterialModel)
async def archive_material(
    material_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    result = await db.database.learning_materials.update_one(
        {"_id": ObjectId(material_id), "user_id": str(current_user.id)},
        {"$set": {"is_archived": True, "updated_at": datetime.now(timezone.utc)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or you don't have permission"
        )
    
    material = await db.database.learning_materials.find_one({"_id": ObjectId(material_id)})
    material["id"] = str(material["_id"])
    del material["_id"]
    
    return LearningMaterialModel(**material)

@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    result = await db.database.learning_materials.delete_one({
        "_id": ObjectId(material_id),
        "user_id": str(current_user.id)
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or you don't have permission"
        )