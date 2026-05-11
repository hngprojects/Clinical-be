from fastapi import APIRouter

from app.api.v1.endpoints import (
	ai_interpretation,
	auth,
	chat,
	health,
	lab_result,
	medical_case,
	notification,
	waitlist,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(medical_case.router)
api_router.include_router(lab_result.router)
api_router.include_router(ai_interpretation.router)
api_router.include_router(chat.router)
api_router.include_router(notification.router)
api_router.include_router(waitlist.router)
