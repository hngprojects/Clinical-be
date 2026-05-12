from __future__ import annotations

import asyncio
import dataclasses
import enum
import html
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

import jinja2

from app.core.exceptions import EmailError
from app.services.mail_transport import send_email_message


class EMAIL_TYPE(enum.Enum):
	OTP = "OTP"
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
	BASE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
	ENV = jinja2.Environment(
		loader=jinja2.FileSystemLoader(str(BASE_DIR)),
		autoescape=jinja2.select_autoescape(["html", "xml"]),
		undefined=jinja2.StrictUndefined,
	)
	TEMPLATES: Dict[EMAIL_TYPE, Dict[str, str]] = {
		EMAIL_TYPE.OTP: {"template": "otp.html", "subject": "Verify your email"},
		EMAIL_TYPE.PASSWORD_RESET: {"template": "password_reset.html", "subject": "Reset Your Clinsight Password"},
		EMAIL_TYPE.PASSWORD_RESET_CONFIRMATION: {
			"template": "password_reset_confirmation.html",
			"subject": "Your Password Has Been Reset",
		},
		EMAIL_TYPE.WAITLIST_INVITE: {"template": "waitlist_invite.html", "subject": "Welcome — your Clinsight invite"},
		EMAIL_TYPE.WELCOME: {"template": "welcome.html", "subject": "Welcome to Clinsight"},
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
		self.provider = provider

	def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
		safe_context: Dict[str, Any] = {}
		for key, value in context.items():
			if isinstance(value, str):
				safe_context[key] = html.escape(value, quote=True)
			else:
				safe_context[key] = value

		if "name" not in safe_context:
			safe_context["name"] = "User"
		if "first_name" not in safe_context:
			safe_context["first_name"] = "User"
		if "code" not in safe_context:
			safe_context["code"] = ""
		if "expires_minutes" not in safe_context:
			safe_context["expires_minutes"] = 10

		cta_url = context.get("cta_url")
		if cta_url is not None:
			parsed = urlparse(str(cta_url))
			if parsed.scheme.lower() in {"http", "https"}:
				safe_context["cta_url"] = html.escape(str(cta_url), quote=True)
			else:
				safe_context["cta_url"] = "#"
		else:
			safe_context["cta_url"] = "#"

		return safe_context

	async def send_email(self, email_type: EMAIL_TYPE, to: str, context: Dict[str, Any]) -> None:
		template_config = TemplatesRegistry.TEMPLATES.get(email_type)
		if template_config is None:
			raise EmailError("Unknown email type")
		try:
			safe_context = self._sanitize_context(context)
			html_body = TemplatesRegistry.ENV.get_template(template_config["template"]).render(**safe_context)
			if self.provider is not None:
				payload = EmailPayload(
					to=to,
					subject=template_config["subject"],
					html=html_body,
					from_email=self.provider.from_email,
					from_name=getattr(self.provider, "from_name", ""),
				)
				await self.provider.send(payload)
				return

			await asyncio.to_thread(
				send_email_message,
				to_email=to,
				subject=template_config["subject"],
				html_body=html_body,
			)
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


async def send_otp_email(to_email: str, first_name: str, code: str, purpose: str, expires_minutes: int = 10) -> None:
	context = {
		"first_name": first_name,
		"code": code,
		"purpose": purpose,
		"expires_minutes": expires_minutes,
	}
	await send_email(EMAIL_TYPE.OTP, to_email, context)


async def send_password_reset_email(to: str, token: str, expires_minutes: int = 10) -> None:
	context = {"name": "", "code": token, "expires_minutes": expires_minutes}
	await send_email(EMAIL_TYPE.PASSWORD_RESET, to, context)


async def send_waitlist_invite_email(to_email: str, name: str, cta_url: str) -> None:
	await send_email(EMAIL_TYPE.WAITLIST_INVITE, to_email, {"name": name, "cta_url": cta_url})


async def send_welcome_email(to_email: str, name: str, cta_url: str) -> None:
	await send_email(EMAIL_TYPE.WELCOME, to_email, {"name": name, "cta_url": cta_url})


def _run_async(coro):
	"""Run async coroutine, handling both cases: with and without existing event loop."""
	try:
		asyncio.get_running_loop()
	except RuntimeError:
		return asyncio.run(coro)
	else:
		import concurrent.futures

		with concurrent.futures.ThreadPoolExecutor() as executor:
			future = executor.submit(asyncio.run, coro)
			return future.result()


def send_password_reset_email_sync(to_email: str, reset_token: str) -> None:
	_run_async(send_password_reset_email(to_email, reset_token))


def send_otp_email_sync(to_email: str, first_name: str, code: str, purpose: str) -> None:
	_run_async(send_otp_email(to_email, first_name, code, purpose))


def send_waitlist_invite_email_sync(to_email: str, name: str, cta_url: str) -> None:
	_run_async(send_waitlist_invite_email(to_email, name, cta_url))


def send_welcome_email_sync(to_email: str, name: str, cta_url: str) -> None:
	_run_async(send_welcome_email(to_email, name, cta_url))
