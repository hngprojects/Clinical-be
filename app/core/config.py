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
	CORS_ORIGINS: list[str]

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

	SMTP_HOST: str = "smtp.gmail.com"
	SMTP_PORT: int = 587
	SMTP_USERNAME: str | None = None
	SMTP_PASSWORD: str | None = None
	SMTP_FROM_EMAIL: str = ""
	SMTP_FROM_NAME: str = "Clinsights"
	ALLOW_STDOUT_EMAIL: bool = False

	@field_validator("SMTP_FROM_EMAIL", mode="after")
	@classmethod
	def smtp_from_email_required_when_smtp_enabled(cls, v: str, info: object) -> str:
		"""Require a non-empty SMTP_FROM_EMAIL when SMTP credentials are configured."""
		data = getattr(info, "data", {})
		if data.get("SMTP_USERNAME") and not v:
			raise ValueError("SMTP_FROM_EMAIL must be set when SMTP_USERNAME is configured")
		return v

	# Password reset
	FRONTEND_RESET_PASSWORD_URL: str
	PASSWORD_RESET_TOKEN_EXPIRES_MINUTES: int = 60


@lru_cache
def get_settings() -> Settings:
	return Settings()  # type: ignore[call-arg]
