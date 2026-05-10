from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import waitlist

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])

#Waitlist Routes
api_router.include_router(                         # ADD
    waitlist.router,
    prefix="/waitlist",
    tags=["waitlist"],
)