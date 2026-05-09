import resend

from app.core.config import settings


def send_password_reset_email(to_email: str, reset_token: str) -> None:
	if not settings.RESEND_API_KEY:
		return
	resend.api_key = settings.RESEND_API_KEY
	link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?token={reset_token}"
	resend.Emails.send(
		{
			"from": settings.EMAIL_FROM,
			"to": to_email,
			"subject": "Reset your password",
			"html": f'<a href="{link}">Reset password</a>',
		},
	)
