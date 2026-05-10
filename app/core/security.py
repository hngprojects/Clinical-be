import bcrypt
import hashlib
import secrets


def hash_opaque_token(raw: str) -> str:
	return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_opaque_token() -> str:
	return secrets.token_urlsafe(32)


def hash_password(plain: str) -> str:
	"""Return a bcrypt hash of `plain`. Safe to store in the database."""
	raw = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12))
	return raw.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
	"""Return True if `plain` matches the stored bcrypt `hashed` value."""
	try:
		return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
	except Exception:
		return False
