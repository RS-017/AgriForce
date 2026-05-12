from twilio.rest import Client
from core.config import settings

_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


async def requestOTP(phone: str) -> dict:
    """Send OTP via Twilio Verify."""
    verification = (
        _client.verify.v2.services(settings.TWILIO_SERVICE_SID)
        .verifications.create(to=phone, channel="sms")
    )
    return {"status": verification.status}


async def verifyOTP(phone: str, code: str) -> bool:
    """Check OTP via Twilio Verify."""
    check = (
        _client.verify.v2.services(settings.TWILIO_SERVICE_SID)
        .verification_checks.create(to=phone, code=code)
    )
    return check.status == "approved"
