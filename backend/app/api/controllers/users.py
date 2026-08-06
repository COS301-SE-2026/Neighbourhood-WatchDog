from uuid import UUID

from fastapi import APIRouter, Depends
from typing import Annotated

from app.core.database import DbSession
from app.auth.dependencies import get_current_user
from app.services.user_service import get_user_by_id_handler

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
async def get_user_by_id(
	user_id: UUID,
	db: DbSession,
	claims: Annotated[dict, Depends(get_current_user)],
) -> dict:
	"""Returns the id, email, cognito_sub, role and created_at of the user with the passed in id"""
	return await get_user_by_id_handler(
		user_id,
		db,
		claims
	)
