# core/validators.py

import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


# ────────────────────────────────────────────────────────────────
# Username validation
#   - 3–25 chars
#   - lowercase a–z, 0–9, dot, underscore
#   - must start/end with alphanumeric
#   - no consecutive dots/underscores
#   - reserved usernames (Ghana-focused)
# ────────────────────────────────────────────────────────────────

USERNAME_REGEX = re.compile(
    r"^[a-z0-9](?:[a-z0-9]|[._](?=[a-z0-9])){1,23}[a-z0-9]$"
)

RESERVED_USERNAMES: set[str] = {
    # Government / institutions / politics (Ghana context)
    "ghanagov",
    "ghana",
    "ghanapolice",
    "gaf",
    "ecg",
    "ecgghana",
    "attorneygeneral",
    "parliamentgh",
    "nationalsecuritygh",
    "ghanacybersecurity",
    "mocgh",  # ministry of communications (if you like)
    # Presidents / major political figures (current & recent)
    "nanaakufoaddo",
    "johndramanimahama",
    "bawumia",
    "jdm",
    "johnmahama",
    # MPs / prominent political voices
    "samgeorge",
    "samuelgeorge",
    "harunai",
    # Major brands & telcos
    "mtn",
    "mtnghana",
    "vodafone",
    "vodafoneghana",
    "airteltigo",
    "melcom",
    "kasapreko",
    "guinnessghana",
    "goldfields",
    "gcb",
    "ecobank",
    "ecobankghana",
    # Media houses
    "citinewsroom",
    "adomtv",
    "utvghana",
    "joynews",
    "ghonetv",
    # Musicians / entertainment
    "sarkodie",
    "shattawale",
    "stonebwoy",
    "blacksherrif",
    "blacko",
    "kingpromise",
    "kidi",
    "kuamieugene",
    "kwesiarthur",
    # Football legends
    "asamoahgyan",
    "babyjet",
    "michaelessien",
    "andreayew",
    "thomaspartey",
    # Faith leaders
    "mensahotabil",
    "archbishopduncanwilliams",
    "bishopdag",
    # Cultural / traditional titles
    "asantehene",
    "otumfuo",
    "gaaman",
    "mantse",
    "okyehene",
    "nananom",
    # Generic system / sensitive names
    "admin",
    "root",
    "system",
    "support",
    "help",
    "moderator",
    "administrator",
    "staff",
    "api",
    "backend",
    "frontend",
    "dashboard",
    "login",
    "logout",
    "signup",
    "settings",
    "superuser",
    "owner",
    "official",
    "verified",
    "koboateng", 
}


username_pattern_validator = RegexValidator(
    regex=USERNAME_REGEX,
    message=_(
        "Invalid username. Use 3–25 lowercase characters: letters, numbers, "
        "dots or underscores. Cannot start or end with dot/underscore, "
        "and no consecutive dots/underscores."
    ),
    code="invalid_username",
)


def validate_username(value: str) -> str:
    """
    Full username validator for use in models/forms/serializers.

    - Normalizes to lowercase & strips whitespace.
    - Blocks reserved usernames (Ghana-focused list).
    - Enforces regex pattern via RegexValidator.
    """
    username = (value or "").lower().strip()

    if username in RESERVED_USERNAMES:
        raise ValidationError(
            _("This username is reserved and cannot be used."),
            code="reserved_username",
        )

    username_pattern_validator(username)
    return username


# ────────────────────────────────────────────────────────────────
# Ghana phone number validation (optional but handy)
#   Accepts:
#       0XXXXXXXXX  (10 digits, local)
#       +233XXXXXXXXX (country code)
# ────────────────────────────────────────────────────────────────

GH_PHONE_REGEX = re.compile(
    r"^(?:0|\+233)(2[0-9]|5[0-9])\d{7}$"
)


ghana_phone_validator = RegexValidator(
    regex=GH_PHONE_REGEX,
    message=_(
        "Enter a valid Ghana phone number starting with 0 or +233 "
        "followed by 9 digits."
    ),
    code="invalid_ghana_phone",
)


def validate_ghana_phone(value: str) -> str:
    """
    Wrapper around ghana_phone_validator so it can be used like
    any other callable validator and can normalize spacing.
    """
    phone = (value or "").strip().replace(" ", "")
    ghana_phone_validator(phone)
    return phone
