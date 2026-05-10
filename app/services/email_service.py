from __future__ import annotations

import dataclasses
import enum
import os
from abc import ABC, abstractmethod
from typing import Any, Dict

import resend

from app.core.exceptions import EmailError


class EMAIL_TYPE(enum.Enum):
	PASSWORD_RESET = "PASSWORD_RESET"
	PASSWORD_RESET_CONFIRMATION = "PASSWORD_RESET_CONFIRMATION"
	WAITLIST_INVITE = "WAITLIST_INVITE"
	WELCOME = "WELCOME"


@dataclasses.dataclass(frozen=True)
class EmailPayload:
	to: str
	subject: str
	html: str
	from_email: str
	from_name: str


class TemplatesRegistry:
	@staticmethod
	def PASSWORD_RESET(context: Dict[str, Any]) -> Dict[str, str]:
		html = f"""
<div style="font-family:Arial,Helvetica,sans-serif;color:#0f172a;padding:24px;">
  <p>Hi {context.get("name", "User")},</p>
  <div style="background:#eef2f7;padding:24px;border-radius:8px;">
    <h1 style="color:#0b5ed7;margin:0 0 12px 0;">Reset Your Password</h1>
    <p>We received a request to reset your Clinsight password. Use the verification code below to continue:</p>
    <p style="font-weight:700;font-size:20px;margin:12px 0;">{context.get("code", "")}</p>
    <p>This code will expire in {context.get("expires_minutes", 10)} minutes.</p>
  </div>
  <p style="margin-top:18px;color:#64748b;font-size:13px;">If you didn't request a password reset, you can safely ignore this email.</p>
</div>
"""
		return {"subject": "Reset Your Clinsight Password", "html": html}

	@staticmethod
	def PASSWORD_RESET_CONFIRMATION(context: Dict[str, Any]) -> Dict[str, str]:
		html = f"""
<div style="font-family:Arial,Helvetica,sans-serif;color:#0f172a;padding:24px;">
  <p>Hi {context.get("name", "User")},</p>
  <div style="background:#eef2f7;padding:24px;border-radius:8px;">
    <h1 style="color:#0b5ed7;margin:0 0 12px 0;">Your Password Has Been Reset</h1>
    <p>Your Clinsight password was successfully reset.</p>
    <p>You can now log in to your account using your new password.</p>
    <p style="margin-top:12px;">If you didn't make this change, please contact support immediately to secure your account.</p>
  </div>
</div>
"""
		return {"subject": "Your Password Has Been Reset", "html": html}

	@staticmethod
	def WAITLIST_INVITE(context: Dict[str, Any]) -> Dict[str, str]:
		cta_url = context.get("cta_url", "#")
		html = f"""
<div style="font-family:Arial,Helvetica,sans-serif;color:#0f172a;padding:24px;">
  <p>Hi {context.get("name", "User")},</p>
  <div style="background:#eef2f7;padding:24px;border-radius:8px;">
    <h1 style="color:#0b5ed7;margin:0 0 12px 0;">You're Invited to Clinsight</h1>
    <p>Thanks for joining the waitlist. We've reserved your spot. Click below to complete signup and get started.</p>
    <p style="margin-top:12px;"><a href="{cta_url}" style="display:inline-block;padding:10px 18px;background:#0b5ed7;color:#fff;border-radius:8px;text-decoration:none;">Sign in to your account</a></p>
  </div>
  <p style="margin-top:18px;color:#64748b;font-size:13px;">If you did not sign up for this account you can ignore this email.</p>
</div>
"""
		return {"subject": "Welcome — your Clinsight invite", "html": html}

	@staticmethod
	def WELCOME(context: Dict[str, Any]) -> Dict[str, str]:
		cta_url = context.get("cta_url", "#")
		html = f"""
<div style="font-family:Arial,Helvetica,sans-serif;color:#0f172a;padding:24px;">
  <p>Hi {context.get("name", "User")},</p>
  <div style="background:#eef2f7;padding:24px;border-radius:8px;">
    <h1 style="color:#0b5ed7;margin:0 0 12px 0;">A big welcome to the Clinsight family</h1>
    <p>Welcome to Clinsight. You can now understand your lab results in seconds.</p>
    <ul>
      <li>Clear explanations in plain language</li>
      <li>Instant risk levels</li>
      <li>Simple next steps you can act on</li>
    </ul>
    <p style="margin-top:12px;"><a href="{cta_url}" style="display:inline-block;padding:10px 18px;background:#0b5ed7;color:#fff;border-radius:8px;text-decoration:none;">Sign in to your account</a></p>
  </div>
</div>
"""
		return {"subject": "Welcome to Clinsight", "html": html}


class EmailProvider(ABC):
	@abstractmethod
	async def send(self, payload: EmailPayload) -> None:
		raise NotImplementedError()


class ResendProvider(EmailProvider):
	def __init__(self, api_key: str, from_email: str, from_name: str) -> None:
		self.api_key = api_key
		self.from_email = from_email
		self.from_name = from_name
		resend.api_key = api_key

	async def send(self, payload: EmailPayload) -> None:
		try:
			resend.Emails.send(
				{
					"from": f"{payload.from_name} <{payload.from_email}>",
					"to": payload.to,
					"subject": payload.subject,
					"html": payload.html,
				}
			)
		except Exception:
			raise EmailError("Failed to deliver email")


class EmailService:
	def __init__(self, provider: EmailProvider | None = None) -> None:
		if provider is not None:
			self.provider = provider
		else:
			api_key = os.getenv("RESEND_API_KEY", "")
			from_email = os.getenv("RESEND_FROM_EMAIL", "")
			from_name = os.getenv("RESEND_FROM_NAME", "")
			if not api_key or not from_email:
				raise EmailError("Email provider not configured")
			self.provider = ResendProvider(api_key=api_key, from_email=from_email, from_name=from_name)

	async def send_email(self, email_type: EMAIL_TYPE, to: str, context: Dict[str, Any]) -> None:
		tpl_func = getattr(TemplatesRegistry, email_type.name, None)
		if tpl_func is None:
			raise EmailError("Unknown email type")
		try:
			built = tpl_func(context)
			payload = EmailPayload(
				to=to,
				subject=built["subject"],
				html=built["html"],
				from_email=self.provider.from_email,
				from_name=getattr(self.provider, "from_name", ""),
			)
			await self.provider.send(payload)
		except EmailError:
			raise
		except Exception:
			raise EmailError("Failed to send email")


_default_service: EmailService | None = None


def _get_service() -> EmailService:
	global _default_service
	if _default_service is None:
		_default_service = EmailService()
	return _default_service


async def send_email(email_type: EMAIL_TYPE, to: str, context: Dict[str, Any]) -> None:
	svc = _get_service()
	await svc.send_email(email_type=email_type, to=to, context=context)


async def send_password_reset_email(to: str, token: str, expires_minutes: int = 10) -> None:
	context = {"name": "", "code": token, "expires_minutes": expires_minutes}
	await send_email(EMAIL_TYPE.PASSWORD_RESET, to, context)
