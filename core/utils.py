import uuid
import io
import math
import hashlib
import requests
from PIL import Image
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from .models import PotholeReport


# -------------------------------------------------------------------
# IMAGE HASHING (pHash)
# -------------------------------------------------------------------
def calculate_phash(image_file) -> str:
    """
    Generate perceptual hash (pHash) for image duplicate detection.
    """
    # Use Image.Resampling.LANCZOS for Pillow 10.0+
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.ANTIALIAS  # Fallback for older Pillow versions
    
    image = Image.open(image_file).convert("L").resize((32, 32), resample_filter)
    pixels = list(image.getdata())
    avg_pixel = sum(pixels) / len(pixels)

    bits = "".join("1" if px >= avg_pixel else "0" for px in pixels)
    hex_hash = f"{int(bits, 2):0x}"

    return hex_hash.zfill(64)  # normalize length


# -------------------------------------------------------------------
# GPS CLUSTERING (Anti-Spam)
# -------------------------------------------------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance (meters) between two GPS points.
    """
    R = 6371000  # Earth radius (meters)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def detect_gps_spam(user, lat, lon, threshold_m=100, recent_minutes=5):
    """
    Block >3 reports in same 100m radius within 5 minutes.
    """

    time_limit = timezone.now() - timezone.timedelta(minutes=recent_minutes)
    recent_reports = PotholeReport.objects.filter(
        user=user, created_at__gte=time_limit
    )

    nearby_count = 0

    for r in recent_reports:
        dist = haversine_distance(lat, lon, r.latitude, r.longitude)
        if dist <= threshold_m:
            nearby_count += 1

    return nearby_count >= 3  # spam if >= 3 recent nearby reports


# -------------------------------------------------------------------
# AI VALIDATION (reject non-pothole images)
# -------------------------------------------------------------------
def ai_validate_pothole(image_file) -> tuple[bool, float]:
    """
    Backend pothole validation.
    If AI_BYPASS=True → automatically approve images during development.
    If False → trust frontend TensorFlow.js severity scoring.
    """

    # Development bypass mode
    if getattr(settings, "AI_BYPASS", False):
        # Always approve with near-perfect confidence
        return True, 0.99

    # --------------------------------------------------------------
    # MVP BACKEND FALLBACK
    # --------------------------------------------------------------
    # Production backend trusts frontend TF.js detection.
    # Later: integrate ONNX model for server-side verification.
    return True, 0.95

    # Future:
    # return run_onnx_model(image_file)


# -------------------------------------------------------------------
# RATE LIMITING (per phone + per IP)
# -------------------------------------------------------------------
def rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """
    Returns True if the user is rate-limited.
    """
    cache_key = f"rl:{key}"
    count = cache.get(cache_key, 0)

    if count >= limit:
        return True

    cache.set(cache_key, count + 1, timeout=window_seconds)
    return False


# -------------------------------------------------------------------
# HELPER: Extract Client IP from Request
# -------------------------------------------------------------------
def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# -------------------------------------------------------------------
# HELPER: Generate Device Fingerprint
# -------------------------------------------------------------------
def generate_device_fingerprint(request):
    ua = request.META.get("HTTP_USER_AGENT", "")
    ip = get_client_ip(request)
    raw = f"{ua}:{ip}"
    return hashlib.sha256(raw.encode()).hexdigest()


# -------------------------------------------------------------------
# AWARD POINTS (Used in admin + Celery)
# -------------------------------------------------------------------
def award_report_points(report: PotholeReport):
    if report.points_awarded > 0:
        return  # Protect from double-crediting

    profile = report.user.profile
    profile.points += 50
    profile.save()

    report.points_awarded = 50
    report.save()


# -------------------------------------------------------------------
# AIRTIME PAYOUT (Africa's Talking)
# -------------------------------------------------------------------
def send_airtime_to_user(phone: str, amount: float) -> tuple[bool, str]:
    """
    Sends MTN airtime using Africa's Talking API.
    Returns (success, reference).
    """

    username = settings.AT_USERNAME
    api_key = settings.AT_API_KEY

    url = "https://api.africastalking.com/version1/airtime/send"
    headers = {
        "apiKey": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "username": username,
        "recipients": f'[{{"phoneNumber":"{phone}","amount":"GHS {amount:.2f}"}}]',
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        data = response.json()

        if data.get("errorMessage"):
            return False, ""

        # Extract reference
        entries = data.get("responses", [])
        if entries:
            return True, entries[0].get("requestId", "")

        return False, ""

    except Exception:
        return False, ""
    


def generate_reference():
    date_part = timezone.now().strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()
    return f"RDM-{date_part}-{random_part}"
