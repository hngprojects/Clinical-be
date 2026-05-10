import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.otp import OtpCode, OtpPurpose


def _generate_numeric_code(length: int) -> str:
	"""Cryptographically random zero-padded numeric code."""
	upper = 10**length
	return f"{secrets.randbelow(upper):0{length}d}"


def _hash_code(code: str) -> str:
	"""Salt the code with the server-side pepper and hash with SHA-256."""
	pepper = settings.OTP_PEPPER.encode("utf-8")
	return hashlib.sha256(pepper + code.encode("utf-8")).hexdigest()


def _codes_match(code: str, code_hash: str) -> bool:
	return hmac.compare_digest(_hash_code(code), code_hash)


async def create_otp_for_user(
	session: AsyncSession,
	*,
	user_id: UUID,
	purpose: OtpPurpose,
) -> tuple[OtpCode, str]:
	"""Invalidate previous active OTPs of `purpose` for the user, then mint a new one.

	Returns the persisted `OtpCode` row and the **plaintext** code (the only
	moment it's available — caller is responsible for delivering it).
	"""
	now = datetime.now(timezone.utc)

	await session.execute(
		update(OtpCode)
		.where(
			OtpCode.user_id == user_id,
			OtpCode.purpose == purpose,
			OtpCode.consumed_at.is_(None),
		)
		.values(consumed_at=now)
	)

	code = _generate_numeric_code(settings.OTP_LENGTH)
	otp = OtpCode(
		user_id=user_id,
		code_hash=_hash_code(code),
		purpose=purpose,
		expires_at=now + timedelta(minutes=settings.OTP_EXPIRES_MINUTES),
	)
	session.add(otp)
	await session.flush()
	return otp, code


class OtpVerificationError(Exception):
	"""Raised when an OTP cannot be verified."""


async def verify_otp_for_user(
	session: AsyncSession,
	*,
	user_id: UUID,
	purpose: OtpPurpose,
	code: str,
) -> OtpCode:
	"""Verify `code` against the latest active OTP for the user/purpose.

	On success the OTP is marked consumed and returned. On failure raises
	`OtpVerificationError` with a user-safe message.
	"""
	now = datetime.now(timezone.utc)

	# Lock the row for the rest of this transaction so concurrent verify
	# requests cannot both read the same `attempts` value and lose increments,
	# which would otherwise let an attacker bypass `OTP_MAX_ATTEMPTS`.
	result = await session.execute(
		select(OtpCode)
		.where(
			OtpCode.user_id == user_id,
			OtpCode.purpose == purpose,
			OtpCode.consumed_at.is_(None),
		)
		.order_by(OtpCode.created_at.desc())
		.limit(1)
		.with_for_update()
	)
	otp = result.scalar_one_or_none()

	if otp is None:
		raise OtpVerificationError("No active code found. Request a new one.")

	if otp.expires_at <= now:
		otp.consumed_at = now
		raise OtpVerificationError("Code has expired. Request a new one.")

	if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
		otp.consumed_at = now
		raise OtpVerificationError("Too many incorrect attempts. Request a new code.")

	if not _codes_match(code, otp.code_hash):
		otp.attempts += 1
		# Burn the code if this attempt put us at the limit.
		if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
			otp.consumed_at = now
		raise OtpVerificationError("Invalid code.")

	otp.consumed_at = now
	return otp
