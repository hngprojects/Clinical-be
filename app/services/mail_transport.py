from __future__ import annotations

import html
import logging
import re
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from smtplib import SMTP, SMTP_SSL

import resend

from app.core.config import Settings, get_settings
from app.core.exceptions import EmailError

logger = logging.getLogger(__name__)

_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def mask_email(email: str) -> str:
	"""Redact the local part of an email address for logs."""
	if "@" in email:
		local, domain = email.split("@", 1)
		return f"{local[:2]}***@{domain}"
	return "***"


def send_email_message(
	*,
	to_email: str,
	subject: str,
	text_body: str | None = None,
	html_body: str | None = None,
	from_email: str | None = None,
	from_name: str | None = None,
	stdout_summary: str | None = None,
) -> None:
	"""Send an email using Resend first, then SMTP, then stdout if enabled."""
	settings = get_settings()
	resolved_from_email = _resolve_from_email(settings, from_email)
	resolved_from_name = _resolve_from_name(settings, from_name)

	if settings.RESEND_API_KEY and settings.RESEND_FROM_EMAIL:
		if resolved_from_email:
			try:
				_send_via_resend(
					settings=settings,
					to_email=to_email,
					subject=subject,
					text_body=text_body,
					html_body=html_body,
					from_email=resolved_from_email,
					from_name=resolved_from_name,
				)
				return
			except EmailError:
				logger.warning("Resend delivery failed; falling back to SMTP", exc_info=True)

	if _smtp_is_configured(settings):
		if not resolved_from_email:
			raise EmailError("SMTP sender address is not configured")
		_send_via_smtp(
			settings=settings,
			to_email=to_email,
			subject=subject,
			text_body=text_body,
			html_body=html_body,
			from_email=resolved_from_email,
			from_name=resolved_from_name,
		)
		return

	if settings.ALLOW_STDOUT_EMAIL:
		if stdout_summary:
			logger.info("STDOUT EMAIL [%s] -> %s", subject, stdout_summary)
		else:
			logger.info("STDOUT EMAIL [%s] -> to: %s", subject, mask_email(to_email))
		return

	raise EmailError("Email service not configured")


def _resolve_from_email(settings: Settings, override: str | None) -> str:
	if override:
		return override.strip()
	for value in (settings.RESEND_FROM_EMAIL, settings.SMTP_FROM_EMAIL):
		if value.strip():
			return value.strip()
	return ""


def _resolve_from_name(settings: Settings, override: str | None) -> str:
	if override:
		return override.strip()
	for value in (settings.RESEND_FROM_NAME, settings.SMTP_FROM_NAME):
		if value.strip():
			return value.strip()
	return ""


def _send_via_resend(
	*,
	settings: Settings,
	to_email: str,
	subject: str,
	text_body: str | None,
	html_body: str | None,
	from_email: str,
	from_name: str,
) -> None:
	resend.api_key = settings.RESEND_API_KEY
	payload: dict[str, object] = {
		"from": formataddr((from_name, from_email)) if from_name else from_email,
		"to": [to_email],
		"subject": subject,
	}
	if text_body:
		payload["text"] = text_body
	if html_body:
		payload["html"] = html_body

	try:
		resend.Emails.send(payload)
	except Exception as exc:
		raise EmailError("Failed to deliver email via Resend") from exc


def _send_via_smtp(
	*,
	settings: Settings,
	to_email: str,
	subject: str,
	text_body: str | None,
	html_body: str | None,
	from_email: str,
	from_name: str,
) -> None:
	host = settings.SMTP_HOST.strip()
	port_raw = settings.SMTP_PORT.strip()
	username = settings.SMTP_USERNAME.strip()
	password = settings.SMTP_PASSWORD
	use_ssl = _is_truthy(settings.SMTP_USE_SSL) or port_raw == "465"
	try:
		port = int(port_raw)
	except ValueError as exc:
		raise EmailError("SMTP_PORT must be a valid integer") from exc

	message = _build_message(
		to_email=to_email,
		subject=subject,
		text_body=text_body,
		html_body=html_body,
		from_email=from_email,
		from_name=from_name,
	)
	context = ssl.create_default_context()

	try:
		if use_ssl:
			with SMTP_SSL(host, port, timeout=10, context=context) as server:
				if username:
					if not password:
						raise EmailError("SMTP credentials are incomplete")
					server.login(username, password)
				server.send_message(message)
		else:
			with SMTP(host, port, timeout=10) as server:
				server.ehlo()
				server.starttls(context=context)
				server.ehlo()
				if username:
					if not password:
						raise EmailError("SMTP credentials are incomplete")
					server.login(username, password)
				server.send_message(message)
	except EmailError:
		raise
	except Exception as exc:
		raise EmailError("Failed to deliver email via SMTP") from exc


def _build_message(
	*,
	to_email: str,
	subject: str,
	text_body: str | None,
	html_body: str | None,
	from_email: str,
	from_name: str,
) -> EmailMessage:
	message = EmailMessage()
	message["To"] = to_email
	message["Subject"] = subject
	message["From"] = formataddr((from_name, from_email)) if from_name else from_email

	plain_text = text_body or _html_to_text(html_body or "")
	if not plain_text:
		plain_text = subject
	message.set_content(plain_text)
	if html_body:
		message.add_alternative(html_body, subtype="html")
	return message


def _html_to_text(value: str) -> str:
	cleaned = re.sub(r"<[^>]+>", " ", value)
	cleaned = html.unescape(cleaned)
	return re.sub(r"\s+", " ", cleaned).strip()


def _smtp_is_configured(settings: Settings | None = None) -> bool:
	settings = settings or get_settings()
	return bool(settings.SMTP_HOST.strip())


def _is_truthy(value: str) -> bool:
	return value.strip().lower() in _TRUTHY_VALUES