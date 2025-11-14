import uuid
import base64
import io
from typing import List, Optional


from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files.base import ContentFile

from ninja import NinjaAPI, Router
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.schema import TokenRefreshInputSchema, TokenRefreshOutputSchema

from .models import (
    UserProfile,
    PotholeReport,
    RedemptionRequest,
    RegionChoices,
)
from .schemas import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserProfileOut,
    IDUploadRequest,
    IDUploadResponse,
    ReportSubmitRequest,
    ReportSubmitResponse,
    PotholeReportOut,
    PotholeMapItem,
    RedeemRequest,
    RedeemResponse,
    RedemptionOut,
    SuccessResponse,
    ErrorResponse,
)
from .utils import (
    calculate_phash,
    detect_gps_spam,
    ai_validate_pothole,
    rate_limit,
    get_client_ip,
    generate_device_fingerprint,
)

User = get_user_model()

api = NinjaAPI(
    title="Pothole Patrol API",
    version="1.0.0",
    urls_namespace="pothole_api",
)

auth_scheme = JWTAuth()

auth_router = Router(tags=["auth"])
reports_router = Router(tags=["reports"])
rewards_router = Router(tags=["rewards"])

# ============================================================
# AUTH: REGISTER
# ============================================================
@auth_router.post("/register", response={200: SuccessResponse, 400: ErrorResponse})
def register(request, payload: RegisterRequest):

    if User.objects.filter(username=payload.username.lower()).exists():
        return 400, ErrorResponse(success=False, message="Username already taken.")

    with transaction.atomic():
        user = User.objects.create_user(
            username=payload.username.lower(),
            password=payload.password
        )
        UserProfile.objects.create(
            user=user,
            phone=payload.phone
        )

    return SuccessResponse(success=True, message="Account created successfully.")


# ============================================================
# AUTH: LOGIN
# ============================================================
@auth_router.post("/login", response={200: AuthResponse, 400: ErrorResponse})
def login(request, payload: LoginRequest):

    user = authenticate(username=payload.username.lower(), password=payload.password)

    if not user:
        return 400, ErrorResponse(success=False, message="Invalid credentials.")

    profile = user.profile

    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    return AuthResponse(
        access=str(access_token),
        refresh=str(refresh),
        user_id=user.id,
        username=user.username,
        phone=profile.phone,
        points=profile.points,
        is_verified=profile.is_verified,
    )


# ============================================================
# AUTH: REFRESH TOKEN
# ============================================================
@auth_router.post("/refresh", response={200: TokenRefreshOutputSchema, 400: ErrorResponse})
def refresh_token(request, payload: TokenRefreshInputSchema):

    try:
        refresh = RefreshToken(payload.refresh)
        new_access = refresh.access_token
        return {"access": str(new_access)}
    except Exception:
        return 400, ErrorResponse(success=False, message="Invalid refresh token.")


# ============================================================
# AUTH: LOGOUT
# ============================================================
@auth_router.post("/logout", response={200: SuccessResponse, 400: ErrorResponse})
def logout(request, payload: TokenRefreshInputSchema):

    try:
        token = RefreshToken(payload.refresh)
        token.blacklist()
        return SuccessResponse(success=True, message="Logged out successfully.")
    except Exception:
        return 400, ErrorResponse(success=False, message="Invalid token.")


# ============================================================
# AUTH: PROFILE
# ============================================================
@auth_router.get("/me", auth=auth_scheme, response=UserProfileOut)
def me(request):

    user = request.auth
    profile = user.profile

    return UserProfileOut(
        user_id=user.id,
        username=user.username,
        phone=profile.phone,
        points=profile.points,
        is_verified=profile.is_verified,
        id_document=profile.id_document.url if profile.id_document else None,
    )


# ============================================================
# AUTH: UPLOAD ID DOCUMENT
# ============================================================
@auth_router.post("/upload-id", auth=auth_scheme,
                  response={200: IDUploadResponse, 400: ErrorResponse})
def upload_id(request, payload: IDUploadRequest):

    user = request.auth
    profile = user.profile

    try:
        base64_data = payload.file_base64.split(",")[-1]
        file_bytes = base64.b64decode(base64_data)
    except Exception:
        return 400, ErrorResponse(success=False, message="Invalid file data.")

    filename = f"id_{uuid.uuid4().hex}.jpg"
    django_file = ContentFile(file_bytes, name=filename)

    profile.id_document = django_file
    profile.is_verified = False  # admin must verify manually
    profile.save()

    return IDUploadResponse(
        message="ID uploaded successfully. Awaiting manual verification.",
        is_verified=profile.is_verified,
        id_document_url=profile.id_document.url,
    )


# ============================================================
# REPORT SUBMISSION
# ============================================================
@reports_router.post("/submit",
    auth=auth_scheme,
    response={200: ReportSubmitResponse, 400: ErrorResponse, 429: ErrorResponse})
def submit_report(request, payload: ReportSubmitRequest):

    user = request.auth
    client_ip = get_client_ip(request)

    # rate limits
    if rate_limit(f"rep:user:{user.id}", limit=3, window_seconds=60):
        return 429, ErrorResponse(success=False, message="Too many reports. Slow down.")
    if rate_limit(f"rep:ip:{client_ip}", limit=10, window_seconds=60):
        return 429, ErrorResponse(success=False, message="Too many reports from this IP.")

    # GPS spam detection
    if detect_gps_spam(user, payload.latitude, payload.longitude):
        return 400, ErrorResponse(
            success=False,
            message="Too many reports around the same location in a short time."
        )

    # Validate region
    if payload.region not in [choice.value for choice in RegionChoices]:
        return 400, ErrorResponse(success=False, message="Invalid region.")

    # Decode image
    try:
        base64_data = payload.image_base64.split(",")[-1]
        raw_image = base64.b64decode(base64_data)
        image_file = io.BytesIO(raw_image)
    except Exception:
        return 400, ErrorResponse(success=False, message="Invalid image data.")

    # pHash
    image_file.seek(0)
    image_hash = calculate_phash(image_file)
    if PotholeReport.objects.filter(image_hash=image_hash).exists():
        return 400, ErrorResponse(success=False, message="Duplicate pothole image.")

    # AI validation
    image_file.seek(0)
    ai_valid, ai_score = ai_validate_pothole(image_file)

    device_id = payload.device_id or generate_device_fingerprint(request)

    filename = f"pothole_{uuid.uuid4().hex}.jpg"
    django_file = ContentFile(raw_image, name=filename)

    report = PotholeReport.objects.create(
        user=user,
        image=django_file,
        image_hash=image_hash,
        latitude=payload.latitude,
        longitude=payload.longitude,
        region=payload.region,
        severity=payload.severity,
        ai_valid=ai_valid,
        ai_score=ai_score,
        is_spam=not ai_valid,
        submitted_ip=client_ip,
        device_id=device_id,
        is_synced=True,
    )

    return ReportSubmitResponse(
        id=report.id,
        status=report.status,
        message="Report submitted successfully and is pending review.",
    )

# ============================================================
# PUBLIC REPORTS
# ============================================================
@reports_router.get("/public", response=List[PotholeMapItem])
def public_reports(request, region: Optional[str] = None):

    qs = PotholeReport.objects.filter(
        status=PotholeReport.Status.APPROVED,
        is_spam=False
    ).order_by("-created_at")

    if region:
        qs = qs.filter(region=region)

    return [
        PotholeMapItem(
            id=r.id,
            region=r.region,
            latitude=r.latitude,
            longitude=r.longitude,
            severity=r.severity,
            created_at=r.created_at,
        )
        for r in qs
    ]


# ============================================================
# MY REPORTS
# ============================================================
@reports_router.get("/mine", auth=auth_scheme, response=List[PotholeReportOut])
def my_reports(request):

    user = request.auth
    qs = PotholeReport.objects.filter(user=user).order_by("-created_at")

    return [
        PotholeReportOut(
            id=r.id,
            user=r.user.username if r.user else None,
            region=r.region,
            latitude=r.latitude,
            longitude=r.longitude,
            severity=r.severity,
            ai_valid=r.ai_valid,
            ai_score=r.ai_score,
            status=r.status,
            is_spam=r.is_spam,
            created_at=r.created_at,
            points_awarded=r.points_awarded,
        )
        for r in qs
    ]


# ============================================================
# REWARDS: REDEEM POINTS
# ============================================================
@rewards_router.post("/redeem",
    auth=auth_scheme,
    response={200: RedeemResponse, 400: ErrorResponse})
def redeem_points(request, payload: RedeemRequest):

    user = request.auth
    profile = user.profile
    points = payload.points

    if points <= 0:
        return 400, ErrorResponse(success=False, message="Points must be positive.")

    if points % 500 != 0:
        return 400, ErrorResponse(success=False, message="Redemptions must be in blocks of 500.")

    if profile.points < points:
        return 400, ErrorResponse(success=False, message="Insufficient points.")

    airtime_amount = (points // 500) * 5

    redemption = RedemptionRequest.objects.create(
        user=user,
        points=points,
        airtime_amount=airtime_amount,
        mtn_phone=payload.mtn_phone,
    )

    return RedeemResponse(
        id=redemption.id,
        status=redemption.status,
        message="Redemption request submitted successfully.",
    )


# ============================================================
# REWARDS: HISTORY
# ============================================================
@rewards_router.get("/history",
    auth=auth_scheme,
    response=List[RedemptionOut])
def redemption_history(request):

    user = request.auth
    qs = RedemptionRequest.objects.filter(user=user).order_by("-created_at")

    return [
        RedemptionOut(
            id=r.id,
            points=r.points,
            airtime_amount=float(r.airtime_amount),
            status=r.status,
            mtn_phone=r.mtn_phone,
            reference=r.reference,
            created_at=r.created_at,
            approved_at=r.approved_at,
        )
        for r in qs
    ]


# ============================================================
# MOUNT ROUTERS
# ============================================================
api.add_router("/auth", auth_router)
api.add_router("/reports", reports_router)
api.add_router("/rewards", rewards_router)
