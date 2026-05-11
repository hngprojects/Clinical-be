import logging

from app.core.celery_app import celery_app
from app.core.exceptions import EmailError
from app.models.otp import OtpPurpose
from app.services.auth.email import send_otp_email
from app.services.email import send_password_reset_email

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_otp_email_task(self, *, to_email: str, first_name: str, code: str, purpose: str) -> None:
	try:
		send_otp_email_sync(to_email=to_email, first_name=first_name, code=code, purpose=purpose)
	except EmailError as exc:
		raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email_task(self, to_email: str, reset_token: str) -> None:
	try:
		send_password_reset_email_sync(to_email, reset_token)
	except EmailError as exc:
		raise self.retry(exc=exc) from exc


def send_otp_email_sync(*, to_email: str, first_name: str, code: str, purpose: str) -> None:
	"""Bridge async OTP sender for Celery."""
	import asyncio

	try:
		purpose_enum = OtpPurpose(purpose)
	except ValueError as exc:
		raise EmailError(message=f"Unknown OTP purpose: {purpose}") from exc

	asyncio.run(
		send_otp_email(
			to_email=to_email,
			first_name=first_name,
			code=code,
			purpose=purpose_enum,
		)
	)


def send_password_reset_email_sync(to_email: str, reset_token: str) -> None:
	"""Bridge async password reset sender for Celery."""
	import asyncio

	asyncio.run(send_password_reset_email(to_email, reset_token))
