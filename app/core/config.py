from functools import lru_cache

from pydantic import Field, PostgresDsn
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

	CORS_ORIGINS: list[str] = ["http://localhost:3000"]

	# JWT
	JWT_SECRET: str = Field(min_length=32)
	JWT_ALGORITHM: str = "HS256"
	JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = 60

	# OTP
	OTP_LENGTH: int = 6
	OTP_EXPIRES_MINUTES: int = 10
	OTP_MAX_ATTEMPTS: int = 5
	OTP_PEPPER: str = Field(min_length=32)

	# Resend (email)
	# When RESEND_API_KEY is not set, ALLOW_STDOUT_EMAIL must be True to log OTPs to stdout.
	RESEND_API_KEY: str | None = None
	ALLOW_STDOUT_EMAIL: bool = False
	RESEND_FROM_EMAIL: str = "onboarding@resend.dev"
	RESEND_FROM_NAME: str = "Clinsights"

	# Password reset
	FRONTEND_RESET_PASSWORD_URL: str = "http://localhost:3000/reset-password"
	EMAIL_FROM: str = "no-reply@clinsights.com"


@lru_cache
def get_settings() -> Settings:
	return Settings()  # type: ignore[call-arg]
