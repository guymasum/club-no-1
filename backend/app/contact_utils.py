import phonenumbers
from phonenumbers import NumberParseException

# Default region used when a phone number is typed without a country code
# (e.g. a waiter enters "79123456" instead of "+25779123456"). Burundi,
# matching the BIF amounts already used throughout bills.py.
DEFAULT_REGION = "BI"


class InvalidPhoneNumber(ValueError):
    """Raised when a phone number can't be parsed/normalized at all."""


def normalize_phone(raw: str) -> str:
    """Normalize a phone number to E.164 (e.g. '+25779123456') — the format
    Twilio and virtually every SMS/WhatsApp API require. Raises
    InvalidPhoneNumber if the input isn't a recognizable number."""
    try:
        parsed = phonenumbers.parse(raw, DEFAULT_REGION)
    except NumberParseException as exc:
        raise InvalidPhoneNumber(f"Numéro de téléphone invalide : {raw}") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhoneNumber(f"Numéro de téléphone invalide : {raw}")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
