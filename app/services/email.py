import logging

import resend

from app.core.config import settings
from app.core.exceptions import EmailError

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_token: str) -> None:
	if not settings.RESEND_API_KEY:
		raise EmailError(message="Email service not configured.")
	resend.api_key = settings.RESEND_API_KEY
	link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?token={reset_token}"

	try:
		resend.Emails.send(
			{
				"from": settings.EMAIL_FROM,
				"to": to_email,
				"subject": "Reset your password",
				"text": f"Reset your password by clicking the link: {link}",
			},
		)
	except Exception as e:
		raise EmailError(message=f"Failed to send password reset email to {to_email}: {e}") from e
