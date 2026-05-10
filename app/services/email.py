import asyncio
import logging
from urllib.parse import urlencode

import resend

from app.core.config import get_settings
from app.core.exceptions import EmailError

logger = logging.getLogger(__name__)


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
	"""Send a password-reset link via Resend.

	Raises EmailError if the API key is not configured or the send fails.
	"""
	settings = get_settings()
	if not settings.RESEND_API_KEY:
		if not settings.ALLOW_STDOUT_EMAIL:
			raise EmailError(message="Email service not configured.")
		else:
			logger.info(f"STDOUT EMAIL [Password Reset] -> to: {to_email}, token: {reset_token}")
			return

	link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?{urlencode({'token': reset_token})}"

	try:
		await asyncio.to_thread(
			resend.Emails.send,
			{
				"from": settings.EMAIL_FROM,
				"to": to_email,
				"subject": "Reset your password",
				"text": f"Reset your password by clicking the link: {link}",
			},
		)
	except Exception as e:
		raise EmailError(message=f"Failed to send password reset email to {to_email}: {e}") from e


async def send_waitlist_email(to_email: str) -> None:
	"""Send a welcome email for joining the waitlist via Resend.

	Raises EmailError if the API key is not configured or the send fails.
	"""
	settings = get_settings()
	if not settings.RESEND_API_KEY:
		if not settings.ALLOW_STDOUT_EMAIL:
			raise EmailError(message="Email service not configured.")
		else:
			logger.info(f"STDOUT EMAIL [Waitlist Welcome] -> to: {to_email}")
			return

	try:
		await asyncio.to_thread(
			resend.Emails.send,
			{
				"from": settings.EMAIL_FROM,
				"to": to_email,
				"subject": "Welcome to our Waitlist!",
				"text": "Thank you for joining our waitlist! We'll be in touch soon.",
			},
		)
	except Exception as e:
		raise EmailError(message=f"Failed to send waitlist email to {to_email}: {e}") from e
