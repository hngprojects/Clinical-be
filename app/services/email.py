import logging
from urllib.parse import urlencode

import resend

from app.core.config import get_settings
from app.core.exceptions import EmailError

logger = logging.getLogger(__name__)


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
	"""Send a password-reset link via Resend.

	Raises EmailError if Resend credentials are not configured or the send fails.
	"""
	settings = get_settings()

	if not settings.RESEND_API_KEY:
		if settings.ALLOW_STDOUT_EMAIL:
			logger.info("STDOUT EMAIL [Password Reset] -> to: %s, token: %s", to_email, reset_token)
			return
		raise EmailError(message="Email service not configured.")

	link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?{urlencode({'token': reset_token})}"

	from_address = (
		f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>"
		if settings.RESEND_FROM_NAME
		else settings.RESEND_FROM_EMAIL
	)

	subject = "Reset your Clinsights password"
	text_body = f"Reset your password by clicking the link below:\n\n{link}\n\nIf you didn't request this, you can safely ignore this email."
	html_body = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto;">
	<h2 style="color: #111;">Reset your password</h2>
	<p style="color: #333; line-height: 1.5;">
		Click the button below to reset your Clinsights password. This link expires in 30 minutes.
	</p>
	<a href="{link}" style="display: inline-block; padding: 12px 24px; background: #2563eb; color: #fff; border-radius: 6px; text-decoration: none; font-weight: 600;">
		Reset password
	</a>
	<p style="color: #666; font-size: 13px; margin-top: 16px;">
		If you didn't request a password reset, you can safely ignore this email.
	</p>
</div>
""".strip()

	try:
		resend.api_key = settings.RESEND_API_KEY
		resend.Emails.send(
			{
				"from": from_address,
				"to": [to_email],
				"subject": subject,
				"text": text_body,
				"html": html_body,
			}
		)
	except Exception as e:
		raise EmailError(message=f"Failed to send password reset email to {to_email}: {e}") from e
