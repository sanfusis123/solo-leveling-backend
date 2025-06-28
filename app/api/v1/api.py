from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, calendar, improvement_log, flashcards, learning_materials, diary, fun_zone, analytics, projects, skills, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(improvement_log.router, prefix="/improvement-log", tags=["improvement"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(flashcards.router, prefix="/flashcards", tags=["flashcards"])
api_router.include_router(learning_materials.router, prefix="/learning-materials", tags=["learning"])
api_router.include_router(diary.router, prefix="/diary", tags=["diary"])
api_router.include_router(fun_zone.router, prefix="/fun-zone", tags=["fun"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])