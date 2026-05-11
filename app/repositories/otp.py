from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.otp import OtpCode, OtpPurpose


class OtpRepository:
	"""Encapsulates all database operations for the OtpCode model."""

	def __init__(self, session: AsyncSession) -> None:
		self._session = session

	async def invalidate_active(
		self,
		*,
		user_id: UUID,
		purpose: OtpPurpose,
		consumed_at: "datetime",
	) -> None:
		"""Mark all unconsumed OTPs for this user+purpose as consumed."""

		await self._session.execute(
			update(OtpCode)
			.where(
				OtpCode.user_id == user_id,
				OtpCode.purpose == purpose,
				OtpCode.consumed_at.is_(None),
			)
			.values(consumed_at=consumed_at)
		)

	def add(self, otp: OtpCode) -> None:
		self._session.add(otp)

	async def flush(self) -> None:
		await self._session.flush()

	async def get_latest_active(
		self,
		*,
		user_id: UUID,
		purpose: OtpPurpose,
		lock: bool = False,
	) -> OtpCode | None:
		"""Return the most recent unconsumed OTP, optionally with a row lock."""
		stmt = (
			select(OtpCode)
			.where(
				OtpCode.user_id == user_id,
				OtpCode.purpose == purpose,
				OtpCode.consumed_at.is_(None),
			)
			.order_by(OtpCode.created_at.desc())
			.limit(1)
		)
		if lock:
			stmt = stmt.with_for_update()

		result = await self._session.execute(stmt)
		return result.scalar_one_or_none()
