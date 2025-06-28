from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.models.flashcard import (
    FlashcardDeck as FlashcardDeckModel,
    Flashcard as FlashcardModel,
    DifficultyLevel
)
from pydantic import BaseModel

router = APIRouter()

class FlashcardDeckCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False

class FlashcardDeckUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

class FlashcardCreate(BaseModel):
    front: str
    back: str
    hint: Optional[str] = None
    tags: List[str] = []
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

class FlashcardUpdate(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    hint: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[DifficultyLevel] = None

class ReviewResult(BaseModel):
    difficulty: int  # 1-5 (1=very hard, 5=very easy)

@router.post("/decks", response_model=FlashcardDeckModel, status_code=status.HTTP_201_CREATED)
async def create_deck(
    deck_in: FlashcardDeckCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    deck_dict = deck_in.model_dump()
    deck_dict["user_id"] = str(current_user.id)
    deck_dict["card_count"] = 0
    deck_dict["created_at"] = datetime.now(timezone.utc)
    deck_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.database.flashcard_decks.insert_one(deck_dict)
    deck_dict["id"] = str(result.inserted_id)
    del deck_dict["_id"]
    
    return FlashcardDeckModel(**deck_dict)

@router.get("/decks", response_model=List[FlashcardDeckModel])
async def get_decks(
    category: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    query = {"$or": [{"user_id": str(current_user.id)}, {"is_public": True}]}
    
    if category:
        query["category"] = category
    if is_public is not None:
        query["is_public"] = is_public
    
    decks = []
    async for deck in db.database.flashcard_decks.find(query).sort("created_at", -1):
        deck["id"] = str(deck["_id"])
        del deck["_id"]
        decks.append(FlashcardDeckModel(**deck))
    
    return decks

@router.get("/decks/{deck_id}", response_model=FlashcardDeckModel)
async def get_deck(
    deck_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    deck = await db.database.flashcard_decks.find_one({
        "_id": ObjectId(deck_id),
        "$or": [{"user_id": str(current_user.id)}, {"is_public": True}]
    })
    
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    deck["id"] = str(deck["_id"])
    del deck["_id"]
    return FlashcardDeckModel(**deck)

@router.put("/decks/{deck_id}", response_model=FlashcardDeckModel)
async def update_deck(
    deck_id: str,
    deck_update: FlashcardDeckUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = deck_update.model_dump(exclude_unset=True)
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await db.database.flashcard_decks.update_one(
            {"_id": ObjectId(deck_id), "user_id": str(current_user.id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found or you don't have permission"
            )
    
    deck = await db.database.flashcard_decks.find_one({"_id": ObjectId(deck_id)})
    deck["id"] = str(deck["_id"])
    del deck["_id"]
    
    return FlashcardDeckModel(**deck)

@router.post("/decks/{deck_id}/cards", response_model=FlashcardModel, status_code=status.HTTP_201_CREATED)
async def create_card(
    deck_id: str,
    card_in: FlashcardCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    # Verify deck ownership
    deck = await db.database.flashcard_decks.find_one({
        "_id": ObjectId(deck_id),
        "user_id": str(current_user.id)
    })
    
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or you don't have permission"
        )
    
    card_dict = card_in.model_dump()
    card_dict["deck_id"] = deck_id
    card_dict["user_id"] = str(current_user.id)
    card_dict["review_count"] = 0
    card_dict["correct_count"] = 0
    card_dict["interval_days"] = 1
    card_dict["ease_factor"] = 2.5
    card_dict["created_at"] = datetime.now(timezone.utc)
    card_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.database.flashcards.insert_one(card_dict)
    card_dict["id"] = str(result.inserted_id)
    
    # Update deck card count
    await db.database.flashcard_decks.update_one(
        {"_id": ObjectId(deck_id)},
        {"$inc": {"card_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    
    del card_dict["_id"]
    return FlashcardModel(**card_dict)

@router.get("/decks/{deck_id}/cards", response_model=List[FlashcardModel])
async def get_cards(
    deck_id: str,
    due_only: bool = Query(False),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Verify deck access
    deck = await db.database.flashcard_decks.find_one({
        "_id": ObjectId(deck_id),
        "$or": [{"user_id": str(current_user.id)}, {"is_public": True}]
    })
    
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    query = {"deck_id": deck_id}
    
    if due_only:
        query["$or"] = [
            {"next_review": None},
            {"next_review": {"$lte": datetime.now(timezone.utc)}}
        ]
    
    cards = []
    async for card in db.database.flashcards.find(query):
        card["id"] = str(card["_id"])
        del card["_id"]
        # Ensure interval_days is an integer
        if "interval_days" in card and isinstance(card["interval_days"], float):
            card["interval_days"] = int(card["interval_days"])
        cards.append(FlashcardModel(**card))
    
    return cards

@router.post("/cards/{card_id}/review", response_model=FlashcardModel)
async def review_card(
    card_id: str,
    review: ReviewResult,
    current_user: UserModel = Depends(get_current_active_user)
):
    card = await db.database.flashcards.find_one({
        "_id": ObjectId(card_id),
        "user_id": str(current_user.id)
    })
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Update spaced repetition algorithm parameters
    ease_factor = card.get("ease_factor", 2.5)
    interval_days = card.get("interval_days", 1)
    
    # Adjust ease factor based on difficulty
    if review.difficulty >= 3:
        ease_factor = ease_factor + 0.1
        correct = True
    else:
        ease_factor = max(1.3, ease_factor - 0.2)
        correct = False
    
    # Calculate next interval
    if review.difficulty == 1:
        interval_days = 1
    elif review.difficulty == 2:
        interval_days = max(1, int(interval_days * 0.6))
    else:
        interval_days = int(interval_days * ease_factor)
    
    next_review = datetime.now(timezone.utc) + timedelta(days=interval_days)
    
    update_data = {
        "review_count": card.get("review_count", 0) + 1,
        "correct_count": card.get("correct_count", 0) + (1 if correct else 0),
        "last_reviewed": datetime.now(timezone.utc),
        "next_review": next_review,
        "interval_days": interval_days,
        "ease_factor": ease_factor,
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.database.flashcards.update_one(
        {"_id": ObjectId(card_id)},
        {"$set": update_data}
    )
    
    card.update(update_data)
    card["id"] = str(card["_id"])
    del card["_id"]
    
    return FlashcardModel(**card)

@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    card = await db.database.flashcards.find_one({
        "_id": ObjectId(card_id),
        "user_id": str(current_user.id)
    })
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    result = await db.database.flashcards.delete_one({"_id": ObjectId(card_id)})
    
    if result.deleted_count > 0:
        # Update deck card count
        await db.database.flashcard_decks.update_one(
            {"_id": ObjectId(card["deck_id"])},
            {"$inc": {"card_count": -1}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        )