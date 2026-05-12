from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from app.api.v1.router import api_router
from app.core.celery_app import configure_celery
from app.core.config import get_settings
from app.core.exceptions import (
	http_exception_handler,
	unhandled_exception_handler,
	validation_exception_handler,
)

settings = get_settings()

if not settings.RESEND_API_KEY and not settings.SMTP_HOST and not settings.ALLOW_STDOUT_EMAIL:
	import warnings

	warnings.warn("No email transport is configured. Set SMTP_HOST, RESEND_API_KEY, or ALLOW_STDOUT_EMAIL.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:  # noqa: ARG001
	configure_celery()
	yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root() -> dict[str, str]:
	return {"message": f"{settings.PROJECT_NAME} is running"}
