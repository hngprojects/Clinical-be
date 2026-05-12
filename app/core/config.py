from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		case_sensitive=True,
		extra="ignore",
	)

	PROJECT_NAME: str = "Clinsights"
	API_V1_PREFIX: str = "/api/v1"

	DATABASE_URL: PostgresDsn

	# CORS
	CORS_ORIGINS: list[str] = Field(default_factory=list)

	# Google OAuth
	GOOGLE_CLIENT_ID: str = ""
	GOOGLE_CLIENT_SECRET: str = ""
	GOOGLE_REDIRECT_URI: str = ""

	# JWT
	JWT_SECRET: str = Field(min_length=32)
	JWT_ALGORITHM: str = "HS256"
	JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = 60

	# OTP
	OTP_LENGTH: int = 6
	OTP_EXPIRES_MINUTES: int = 10
	OTP_MAX_ATTEMPTS: int = 5
	OTP_PEPPER: str = Field(min_length=32)

	RESEND_API_KEY: str | None = None
	RESEND_FROM_EMAIL: str = ""
	RESEND_FROM_NAME: str = "Clinsights"
	ALLOW_STDOUT_EMAIL: bool = False

	CELERY_BROKER_URL: str = "redis://localhost:6379/0"
	CELERY_RESULT_BACKEND: str | None = None

	@field_validator("RESEND_FROM_EMAIL", mode="after")
	@classmethod
	def resend_from_email_required_when_resend_enabled(cls, v: str, info: object) -> str:
		"""Require a non-empty RESEND_FROM_EMAIL when Resend is configured."""
		data = getattr(info, "data", {})
		if data.get("RESEND_API_KEY") and not v:
			raise ValueError("RESEND_FROM_EMAIL must be set when RESEND_API_KEY is configured")
		return v

	# Password reset
	FRONTEND_RESET_PASSWORD_URL: str = ""
	PASSWORD_RESET_TOKEN_EXPIRES_MINUTES: int = 60

	# AI interpretation
	AI_PROVIDER: str = "gemini"
	AI_MODEL: str = "gemini-1.5-flash"
	AI_TEMPERATURE: float = 0.2
	AI_MAX_RETRIES: int = 2
	AI_TIMEOUT_SECONDS: int = 30
	GEMINI_API_KEY: str | None = None
	OPENAI_API_KEY: str | None = None


@lru_cache
def get_settings() -> Settings:
	return Settings()  # type: ignore[call-arg]
