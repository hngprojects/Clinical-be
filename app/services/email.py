import logging
from urllib.parse import urlencode

from app.core.config import get_settings
from app.core.exceptions import EmailError
from app.services.mail_transport import mask_email, send_email_message

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_token: str) -> None:
	"""Send a password-reset link through the configured mail transport.

	Raises EmailError if no mail transport is configured or the send fails.
	"""
	settings = get_settings()

	link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?{urlencode({'token': reset_token})}"

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
		send_email_message(
			to_email=to_email,
			subject=subject,
			text_body=text_body,
			html_body=html_body,
			stdout_summary=f"to: {mask_email(to_email)}, token: [REDACTED]",
		)
	except EmailError as e:
		raise EmailError(message=f"Failed to send password reset email: {e}") from e


def send_contact_feedback_email(full_name: str, to_email: str, message: str) -> None:
	"""Send a feedback acknowledgement email to the contact form submitter."""
	subject = "We received your message — Clinsights"
	text_body = (
		f"Hi {full_name},\n\n"
		"Thank you for reaching out! We've received your message and will get back to you shortly.\n\n"
		f"Your message:\n{message}\n\n"
		"— The Clinsights Team"
	)
	html_body = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto;">
	<h2 style="color: #111;">Thanks for reaching out, {full_name}!</h2>
	<p style="color: #333; line-height: 1.5;">
		We've received your message and will get back to you shortly.
	</p>
	<div style="background: #f4f4f5; border-radius: 6px; padding: 16px; margin: 16px 0;">
		<p style="color: #555; font-size: 14px; margin: 0; white-space: pre-wrap;">{message}</p>
	</div>
	<p style="color: #666; font-size: 13px;">— The Clinsights Team</p>
</div>
""".strip()

	try:
		send_email_message(
			to_email=to_email,
			subject=subject,
			text_body=text_body,
			html_body=html_body,
			stdout_summary=f"to: {mask_email(to_email)}, name: {full_name}",
		)
	except EmailError as e:
		raise EmailError(message=f"Failed to send contact feedback email: {e}") from e


