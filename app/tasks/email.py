import logging

from celery import shared_task

from app.models.otp import OtpPurpose
from app.services.auth.email import send_otp_email
from app.services.email import send_password_reset_email

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_otp_email_task(self, *, to_email: str, first_name: str, code: str, purpose: str) -> None:
	try:
		purpose_enum = OtpPurpose(purpose)
	except ValueError:
		logger.error("Unknown OTP purpose: %s", purpose)
		return

	try:
		send_otp_email(to_email=to_email, first_name=first_name, code=code, purpose=purpose_enum)
	except Exception as exc:
		logger.warning("OTP email task failed (retrying): %s", exc, exc_info=True)
		raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email_task(self, to_email: str, reset_token: str) -> None:
	try:
		send_password_reset_email(to_email, reset_token)
	except Exception as exc:
		logger.warning("Password reset email task failed (retrying): %s", exc, exc_info=True)
		raise self.retry(exc=exc) from exc
