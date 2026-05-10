import logging
import os

import resend

logger = logging.getLogger(__name__)


async def send_waitlist_welcome(email: str) -> None:
    """Send a welcome email to a new waitlist signup."""

    resend.api_key = os.environ["RESEND_API_KEY"]  # read at call time, not import time

    resend.Emails.send({
        "from": "Clinical App <onboarding@resend.dev>",
        "to": email,
        "subject": "You're on the waitlist!",
        "html": f"""
            <h2>You're in!</h2>
            <p>Thanks for joining the waitlist. We'll reach out to
            <strong>{email}</strong> as soon as a spot opens up.</p>
            <p>— The Clinical Team</p>
        """,
    })