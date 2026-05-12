"""
Clinsights — Smoke Test Suite

Run against a live server:
	pytest tests/smoke_test.py -v --base-url=http://localhost:8000

Full happy-path (needs a real OTP from server stdout):
	TEST_OTP=123456 pytest tests/smoke_test.py -v --base-url=http://localhost:8000

Deps:  pytest  httpx  faker
Install: uv add --dev pytest httpx faker
     or: pip install pytest httpx faker
"""

import os
import uuid

import httpx
import pytest
from faker import Faker

fake = Faker()


def _base() -> str:
	return os.getenv("TEST_BASE_URL", "http://localhost:8000")

def API(path: str) -> str:
	return f"{_base()}/api/v1{path}"

# Shared mutable state threaded through ordered tests
_state: dict = {}

def unique_email() -> str:
	return f"smoke+{uuid.uuid4().hex[:8]}@clinsights-test.dev"

def assert_success(res: httpx.Response, expected_status: int = 200) -> dict:
	assert res.status_code == expected_status, (
		f"Expected {expected_status}, got {res.status_code}. Body: {res.text}"
	)
	body = res.json()
	assert "message" in body, f"Missing 'message' field: {body}"
	return body

def auth_headers(token: str) -> dict:
	return {"Authorization": f"Bearer {token}"}

class TestHealth:
	def test_health_ok(self):
		res = httpx.get(API("/health"))
		assert res.status_code == 200
		assert res.json().get("status") == "ok"

	def test_root_ok(self):
		res = httpx.get(_base())
		assert res.status_code == 200
		assert "message" in res.json()

class TestSignup:
	def test_signup_valid(self):
		email = unique_email()
		_state["email"] = email
		_state["password"] = "Secure@1234"
		res = httpx.post(API("/auth/signup"), json={
			"first_name": fake.first_name(),
			"last_name": fake.last_name(),
			"email": email,
			"password": "Secure@1234",
			"confirm_password": "Secure@1234",
		})
		body = assert_success(res, 201)
		assert body["data"]["email"] == email
		assert "expires_in_seconds" in body["data"]

	def test_signup_duplicate_verified_is_409(self):
		pre_verified = _state.get("verified_email")
		if not pre_verified:
			pytest.skip("No verified user in state yet — run full suite with TEST_OTP set")
		res = httpx.post(API("/auth/signup"), json={
			"first_name": "Dup",
			"last_name": "User",
			"email": pre_verified,
			"password": "Secure@1234",
			"confirm_password": "Secure@1234",
		})
		assert res.status_code == 409

	def test_signup_password_mismatch_is_422(self):
		res = httpx.post(API("/auth/signup"), json={
			"first_name": "Test",
			"last_name": "User",
			"email": unique_email(),
			"password": "Secure@1234",
			"confirm_password": "Different@1234",
		})
		assert res.status_code == 422

	def test_signup_short_password_is_422(self):
		res = httpx.post(API("/auth/signup"), json={
			"first_name": "Test",
			"last_name": "User",
			"email": unique_email(),
			"password": "short",
			"confirm_password": "short",
		})
		assert res.status_code == 422

	def test_signup_invalid_email_is_422(self):
		res = httpx.post(API("/auth/signup"), json={
			"first_name": "Test",
			"last_name": "User",
			"email": "not-an-email",
			"password": "Secure@1234",
			"confirm_password": "Secure@1234",
		})
		assert res.status_code == 422

	def test_signup_missing_fields_is_422(self):
		res = httpx.post(API("/auth/signup"), json={"email": unique_email()})
		assert res.status_code == 422


class TestOtp:
	def test_verify_otp_wrong_code_is_401(self):
		email = _state.get("email")
		if not email:
			pytest.skip("No email in state")
		res = httpx.post(API("/auth/verify-otp"), json={
			"email": email,
			"code": "000000",
		})
		assert res.status_code == 401

	def test_resend_otp_valid(self):
		email = _state.get("email")
		if not email:
			pytest.skip("No email in state")
		res = httpx.post(API("/auth/resend-otp"), json={"email": email})
		body = assert_success(res, 200)
		assert body["data"]["email"] == email

	def test_resend_otp_unknown_email_is_404(self):
		res = httpx.post(API("/auth/resend-otp"), json={"email": "nobody@nowhere.dev"})
		assert res.status_code == 404

	def test_verify_otp_unknown_email_is_401(self):
		res = httpx.post(API("/auth/verify-otp"), json={
			"email": "ghost@nobody.dev",
			"code": "123456",
		})
		assert res.status_code == 401

class TestLoginUnverified:
	def test_login_unverified_user_is_403(self):
		email = _state.get("email")
		if not email:
			pytest.skip("No email in state")
		res = httpx.post(API("/auth/login"), json={
			"email": email,
			"password": "Secure@1234",
		})
		assert res.status_code == 403

	def test_login_unknown_email_is_404(self):
		res = httpx.post(API("/auth/login"), json={
			"email": "ghost@nobody.dev",
			"password": "Whatever@1234",
		})
		assert res.status_code == 404

	def test_login_missing_password_is_422(self):
		res = httpx.post(API("/auth/login"), json={"email": unique_email()})
		assert res.status_code == 422

class TestProtectedRoutes:
	def test_me_no_token_is_401(self):
		res = httpx.get(API("/auth/me"))
		assert res.status_code == 401

	def test_me_bad_token_is_401(self):
		res = httpx.get(API("/auth/me"), headers={"Authorization": "Bearer bad.token.here"})
		assert res.status_code == 401

	def test_me_malformed_header_is_401(self):
		res = httpx.get(API("/auth/me"), headers={"Authorization": "Token notbearer"})
		assert res.status_code == 401

class TestForgotPassword:
	def test_forgot_password_known_email_is_200(self):
		email = _state.get("email")
		if not email:
			pytest.skip("No email in state")
		res = httpx.post(API("/auth/forgot-password"), json={"email": email})
		assert res.status_code == 200

	def test_forgot_password_unknown_email_still_200(self):
		"""Anti-enumeration: unknown emails must NOT return 404."""
		res = httpx.post(API("/auth/forgot-password"), json={"email": "ghost@nobody.dev"})
		assert res.status_code == 200

	def test_forgot_password_invalid_email_is_422(self):
		res = httpx.post(API("/auth/forgot-password"), json={"email": "not-an-email"})
		assert res.status_code == 422

	def test_reset_password_invalid_token_is_4xx(self):
		res = httpx.post(API("/auth/reset-password"), json={
			"token": "a" * 20,
			"new_password": "NewSecure@5678",
		})
		assert res.status_code in (400, 401, 404, 422)

	def test_reset_password_token_too_short_is_422(self):
		res = httpx.post(API("/auth/reset-password"), json={
			"token": "short",
			"new_password": "NewSecure@5678",
		})
		assert res.status_code == 422


class TestGoogleOAuth:
	def test_google_login_redirects(self):
		res = httpx.get(API("/auth/google"), follow_redirects=False)
		assert res.status_code in (302, 307)
		assert "accounts.google.com" in res.headers.get("location", "")

	def test_google_callback_no_code_is_422(self):
		res = httpx.get(API("/auth/google/callback"))
		assert res.status_code == 422

	def test_google_callback_bad_code_is_4xx(self):
		res = httpx.get(API("/auth/google/callback"), params={"code": "invalid_code"})
		assert res.status_code in (400, 401, 422, 500)


REAL_OTP = os.getenv("TEST_OTP", "")

@pytest.mark.skipif(not REAL_OTP, reason="TEST_OTP not set — skipping full happy-path")
class TestHappyPath:
	_email: str = ""
	_token: str = ""

	def test_01_signup(self):
		TestHappyPath._email = unique_email()
		res = httpx.post(API("/auth/signup"), json={
			"first_name": "Happy",
			"last_name": "Path",
			"email": TestHappyPath._email,
			"password": "Secure@1234",
			"confirm_password": "Secure@1234",
		})
		assert_success(res, 201)

	def test_02_verify_otp(self):
		res = httpx.post(API("/auth/verify-otp"), json={
			"email": TestHappyPath._email,
			"code": REAL_OTP,
		})
		body = assert_success(res, 200)
		TestHappyPath._token = body["data"]["access_token"]
		_state["verified_email"] = TestHappyPath._email
		_state["token"] = TestHappyPath._token

	def test_03_me(self):
		res = httpx.get(API("/auth/me"), headers=auth_headers(TestHappyPath._token))
		body = assert_success(res, 200)
		assert body["data"]["email"] == TestHappyPath._email

	def test_04_login(self):
		res = httpx.post(API("/auth/login"), json={
			"email": TestHappyPath._email,
			"password": "Secure@1234",
		})
		body = assert_success(res, 200)
		assert "access_token" in body["data"]

	def test_05_resend_on_verified_is_409(self):
		res = httpx.post(API("/auth/resend-otp"), json={"email": TestHappyPath._email})
		assert res.status_code == 409

	def test_06_wrong_password_is_401(self):
		res = httpx.post(API("/auth/login"), json={
			"email": TestHappyPath._email,
			"password": "WrongPass@999",
		})
		assert res.status_code == 401

	def test_07_reset_with_stale_token_is_4xx(self):
		httpx.post(API("/auth/forgot-password"), json={"email": TestHappyPath._email})
		res = httpx.post(API("/auth/reset-password"), json={
			"token": "a" * 32,
			"new_password": "NewSecure@999",
		})
		assert res.status_code in (400, 401, 404)