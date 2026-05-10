import asyncio
import html
import logging

import resend

from app.core.config import get_settings
from app.models.otp import OtpPurpose

logger = logging.getLogger(__name__)


_PURPOSE_SUBJECTS: dict[OtpPurpose, str] = {
	OtpPurpose.EMAIL_VERIFICATION: "Verify your email",
}

_PURPOSE_INTROS: dict[OtpPurpose, str] = {
	OtpPurpose.EMAIL_VERIFICATION: (
		"Welcome to Clinsights! Use the code below to verify your email and finish creating your account."
	),
}


def _render_html(first_name: str, code: str, purpose: OtpPurpose, expires_minutes: int) -> str:
	intro = _PURPOSE_INTROS[purpose]
	safe_first_name = html.escape(first_name, quote=True)
	safe_code = html.escape(code, quote=True)
	return f"""
	<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto;">
		<h2 style="color: #111;">Hi {safe_first_name},</h2>
		<p style="color: #333; line-height: 1.5;">{intro}</p>
		<div style="font-size: 32px; font-weight: 700; letter-spacing: 8px; padding: 16px 24px; background: #f4f6fb; border-radius: 8px; text-align: center; color: #111;">
			{safe_code}
		</div>
		<p style="color: #666; font-size: 14px; margin-top: 16px;">
			This code expires in {expires_minutes} minutes. If you didn't request it, you can safely ignore this email.
		</p>
	</div>
	""".strip()


def _render_text(first_name: str, code: str, purpose: OtpPurpose, expires_minutes: int) -> str:
	intro = _PURPOSE_INTROS[purpose]
	return (
		f"Hi {first_name},\n\n"
		f"{intro}\n\n"
		f"Your code: {code}\n\n"
		f"This code expires in {expires_minutes} minutes. "
		"If you didn't request it, you can ignore this email."
	)


async def send_otp_email(*, to_email: str, first_name: str, code: str, purpose: OtpPurpose) -> None:
	"""Send the OTP to the user via Resend (or log it in dev mode)."""
	if purpose is not OtpPurpose.EMAIL_VERIFICATION:
		raise ValueError("OTP email is only supported for email verification.")

	settings = get_settings()
	expires_minutes = settings.OTP_EXPIRES_MINUTES
	subject = _PURPOSE_SUBJECTS[purpose]
	html_body = _render_html(first_name, code, purpose, expires_minutes)
	text = _render_text(first_name, code, purpose, expires_minutes)

	if not settings.RESEND_API_KEY:
		if settings.ALLOW_STDOUT_EMAIL:
			logger.info(
				"STDOUT EMAIL [OTP] -> to: %s, purpose: %s, code: %s",
				to_email,
				purpose.value,
				code,
			)
		else:
			logger.warning(
				"RESEND_API_KEY not set and ALLOW_STDOUT_EMAIL is False. OTP email to %s (purpose=%s) failed.",
				to_email,
				purpose.value,
			)
		return

	from_address = (
		f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>"
		if settings.RESEND_FROM_NAME
		else settings.RESEND_FROM_EMAIL
	)
	try:
		await asyncio.to_thread(
			resend.Emails.send,
			{
				"from": from_address,
				"to": [to_email],
				"subject": subject,
				"html": html_body,
				"text": text,
			},
		)
	except Exception:
		logger.exception("Failed to send OTP email to %s (purpose=%s)", to_email, purpose.value)
		raise
