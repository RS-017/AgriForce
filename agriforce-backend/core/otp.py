"""core/otp.py — In-memory OTP service (no external provider)."""
from __future__ import annotations

import random
import time

# Store: phone -> (otp_code, expires_at_epoch)
_otp_store: dict[str, tuple[str, float]] = {}

OTP_TTL_SECONDS = 300  # 5 minutes


def _generate_otp() -> str:
    return str(random.randint(100000, 999999))


async def requestOTP(phone: str) -> dict:
    """Generate a 6-digit OTP and store it in memory."""
    code = _generate_otp()
    expires_at = time.time() + OTP_TTL_SECONDS
    _otp_store[phone] = (code, expires_at)

    # In development: print to console so you can use it
    print(f"\n[OTP] Phone: {phone}  Code: {code}  (valid 5 min)\n")

    return {"status": "pending"}


async def verifyOTP(phone: str, code: str) -> bool:
    """Validate OTP. Returns True if correct and not expired."""
    entry = _otp_store.get(phone)
    if not entry:
        return False

    stored_code, expires_at = entry
    if time.time() > expires_at:
        del _otp_store[phone]
        return False

    if stored_code != code.strip():
        return False

    # Consume the OTP so it cannot be reused
    del _otp_store[phone]
    return True
