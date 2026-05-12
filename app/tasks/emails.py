import logging

from celery import shared_task

from app.services.email_service import (
	send_otp_email_sync,
	send_password_reset_email_sync,
	send_waitlist_invite_email_sync,
	send_welcome_email_sync,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_otp_email_task(self, to_email: str, first_name: str, code: str, purpose: str) -> None:
	try:
		send_otp_email_sync(to_email, first_name, code, purpose)
	except Exception as exc:
		logger.warning("OTP email task failed (retrying): %s", exc, exc_info=True)
		raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email_task(self, to_email: str, reset_token: str) -> None:
	try:
		send_password_reset_email_sync(to_email, reset_token)
	except Exception as exc:
		logger.warning("Password reset email task failed (retrying): %s", exc, exc_info=True)
		raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_waitlist_invite_email_task(self, to_email: str, name: str, cta_url: str) -> None:
	try:
		send_waitlist_invite_email_sync(to_email, name, cta_url)
	except Exception as exc:
		logger.warning("Waitlist invite email task failed (retrying): %s", exc, exc_info=True)
		raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_welcome_email_task(self, to_email: str, name: str, cta_url: str) -> None:
	try:
		send_welcome_email_sync(to_email, name, cta_url)
	except Exception as exc:
		logger.warning("Welcome email task failed (retrying): %s", exc, exc_info=True)
		raise self.retry(exc=exc) from exc
