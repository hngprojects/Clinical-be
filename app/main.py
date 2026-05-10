from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
	http_exception_handler,
	unhandled_exception_handler,
	validation_exception_handler,
)

settings = get_settings()

if settings.RESEND_API_KEY:
	import resend

	resend.api_key = settings.RESEND_API_KEY
elif not settings.ALLOW_STDOUT_EMAIL:
	import warnings

	warnings.warn("RESEND_API_KEY is not set and ALLOW_STDOUT_EMAIL is False. Emails will fail.")

app = FastAPI(title=settings.PROJECT_NAME)

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
