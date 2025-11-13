from decouple import config

# ────────────────────────────────────────────────────────────────
# Determine active environment (dev, prod)
# ────────────────────────────────────────────────────────────────
ENVIRONMENT = config("DJANGO_ENV", default="dev").strip().lower()

# Sanity check: only allow known environments
VALID_ENVIRONMENTS = {"dev", "prod"}

if ENVIRONMENT not in VALID_ENVIRONMENTS:
    raise ValueError(
        f"Invalid DJANGO_ENV='{ENVIRONMENT}'. "
        f"Must be one of: {', '.join(VALID_ENVIRONMENTS)}"
    )

# ────────────────────────────────────────────────────────────────
# Load settings based on environment
# ────────────────────────────────────────────────────────────────
if ENVIRONMENT == "prod":
    from .prod import *
else:
    from .dev import *

# Optional: set a global identifier
ACTIVE_ENV = ENVIRONMENT
