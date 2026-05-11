from __future__ import annotations

import dataclasses
import enum
import html
import os
from abc import ABC, abstractmethod
from typing import Any, Dict
from urllib.parse import urlparse

import jinja2
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
	_env = None
	_template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", "emails"))

	try:
		_env = jinja2.Environment(
			loader=jinja2.FileSystemLoader(_template_dir),
			autoescape=jinja2.select_autoescape(["html", "xml"]),
			undefined=jinja2.StrictUndefined,
		)
	except Exception:
		_env = None

	@staticmethod
	def PASSWORD_RESET(context: Dict[str, Any]) -> Dict[str, str]:
		tpl = TemplatesRegistry._env.get_template("password_reset.html")
		html_out = tpl.render(**context)
		return {"subject": "Reset Your Clinsight Password", "html": html_out}

	@staticmethod
	def PASSWORD_RESET_CONFIRMATION(context: Dict[str, Any]) -> Dict[str, str]:
		tpl = TemplatesRegistry._env.get_template("password_reset_confirmation.html")
		html_out = tpl.render(**context)
		return {"subject": "Your Password Has Been Reset", "html": html_out}

	@staticmethod
	def WAITLIST_INVITE(context: Dict[str, Any]) -> Dict[str, str]:
		tpl = TemplatesRegistry._env.get_template("waitlist_invite.html")
		html_out = tpl.render(**context)
		return {"subject": "Welcome — your Clinsight invite", "html": html_out}

	@staticmethod
	def WELCOME(context: Dict[str, Any]) -> Dict[str, str]:
		tpl = TemplatesRegistry._env.get_template("welcome.html")
		html_out = tpl.render(**context)
		return {"subject": "Welcome to Clinsight", "html": html_out}


# map EMAIL_TYPE to template builders
TEMPLATES: Dict[EMAIL_TYPE, Any] = {
	EMAIL_TYPE.PASSWORD_RESET: TemplatesRegistry.PASSWORD_RESET,
	EMAIL_TYPE.PASSWORD_RESET_CONFIRMATION: TemplatesRegistry.PASSWORD_RESET_CONFIRMATION,
	EMAIL_TYPE.WAITLIST_INVITE: TemplatesRegistry.WAITLIST_INVITE,
	EMAIL_TYPE.WELCOME: TemplatesRegistry.WELCOME,
}


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
			await resend.Emails.send_async(
				{
					"from": f"{payload.from_name} <{payload.from_email}>",
					"to": payload.to,
					"subject": payload.subject,
					"html": payload.html,
				}
			)
		except Exception as e:
			raise EmailError("Failed to deliver email") from e


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
		tpl_func = TEMPLATES.get(email_type)
		if tpl_func is None:
			raise EmailError("Unknown email type")
		try:
			# sanitize context: escape user-controlled values and validate cta_url scheme
			sanitized: Dict[str, Any] = {}
			name = context.get("name")
			sanitized["name"] = html.escape(str(name)) if name else "User"
			code = context.get("code")
			sanitized["code"] = html.escape(str(code)) if code else ""
			expires_minutes = context.get("expires_minutes")
			try:
				sanitized["expires_minutes"] = int(expires_minutes) if expires_minutes is not None else 10
			except Exception:
				sanitized["expires_minutes"] = 10
			cta = context.get("cta_url")
			if cta:
				parsed = urlparse(str(cta))
				if parsed.scheme and parsed.scheme.lower() in ("http", "https"):
					sanitized["cta_url"] = html.escape(str(cta), quote=True)
				else:
					sanitized["cta_url"] = "#"
			else:
				sanitized["cta_url"] = "#"

			built = tpl_func(sanitized)
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
		except Exception as e:
			raise EmailError("Failed to send email") from e


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
