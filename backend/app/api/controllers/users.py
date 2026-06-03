from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.core.database import DbSession
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
async def get_user_by_id(
	user_id: UUID,
	db: DbSession,
	claims: dict = Depends(get_current_user),
):
	_ = claims

	if not db:
		raise HTTPException(status_code=500, detail="No database session")

	user = db.get(User, user_id)
	if not user:
		raise HTTPException(status_code=404, detail="User not found")

	return {
		"id": str(user.id),
		"email": user.email,
		"first_name": user.first_name,
		"last_name": user.last_name,
		"cognito_sub": user.cognito_sub,
		"role": user.role.value if hasattr(user.role, "value") else str(user.role),
		"neighbourhood_id": str(user.neighbourhood_id) if user.neighbourhood_id else None,
		"created_at": user.created_at,
	}
