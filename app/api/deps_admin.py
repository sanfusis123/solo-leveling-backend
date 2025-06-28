from fastapi import Depends, HTTPException, status
from app.models.user import UserModel
from app.api.deps import get_current_active_user

async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Get current admin user.
    Raises HTTPException if user is not an admin.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user