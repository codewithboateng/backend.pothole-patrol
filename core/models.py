import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser

from core.validators import validate_username, validate_ghana_phone


# ────────────────────────────────────────────────────────────────
# Custom User Model (Production Level)
# ────────────────────────────────────────────────────────────────
class User(AbstractUser):
    """
    Custom user model for production.
    Username-based login with Ghana-focused validation rules.
    """

    username = models.CharField(
        max_length=25,
        unique=True,
        validators=[validate_username],
        help_text="3–25 chars, lowercase, letters/numbers/dot/underscore only."
    )

    # Remove name fields if not needed
    first_name = None
    last_name = None
    
     # FIX: override groups + permissions related_name to avoid clashes
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="core_users",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="core_users_permissions",
        blank=True,
    )


    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.lower().strip()
        super().save(*args, **kwargs)


# ────────────────────────────────────────────────────────────────
# TimeStamped Abstract Base Model
# ────────────────────────────────────────────────────────────────
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ────────────────────────────────────────────────────────────────
# User Profile
# ────────────────────────────────────────────────────────────────
class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    phone = models.CharField(
        max_length=20,
        validators=[validate_ghana_phone],
    )

    is_verified = models.BooleanField(default=False)
    id_document = models.FileField(upload_to="ids/", null=True, blank=True)

    # Reserved or celebrity account
    is_protected = models.BooleanField(default=False)

    points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username


# ────────────────────────────────────────────────────────────────
# Region Choices
# ────────────────────────────────────────────────────────────────
class RegionChoices(models.TextChoices):
    GREATER_ACCRA = "Greater Accra", "Greater Accra"
    ASHANTI = "Ashanti", "Ashanti"
    EASTERN = "Eastern", "Eastern"
    WESTERN = "Western", "Western"
    WESTERN_NORTH = "Western North", "Western North"
    CENTRAL = "Central", "Central"
    VOLTA = "Volta", "Volta"
    OTI = "Oti", "Oti"
    NORTHERN = "Northern", "Northern"
    SAVANNAH = "Savannah", "Savannah"
    NORTH_EAST = "North East", "North East"
    UPPER_EAST = "Upper East", "Upper East"
    UPPER_WEST = "Upper West", "Upper West"
    BONO = "Bono", "Bono"
    BONO_EAST = "Bono East", "Bono East"
    AHAFO = "Ahafo", "Ahafo"


# ────────────────────────────────────────────────────────────────
# Pothole Report
# ────────────────────────────────────────────────────────────────
class PotholeReport(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pothole_reports",
    )

    image = models.ImageField(upload_to="potholes/")
    image_hash = models.CharField(max_length=64, db_index=True)

    latitude = models.FloatField()
    longitude = models.FloatField()
    region = models.CharField(
        max_length=50,
        choices=RegionChoices.choices,
        default=RegionChoices.GREATER_ACCRA,
    )

    severity = models.PositiveSmallIntegerField()
    ai_valid = models.BooleanField(default=True)
    ai_score = models.FloatField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    is_spam = models.BooleanField(default=False)

    submitted_ip = models.GenericIPAddressField(null=True, blank=True)
    device_id = models.CharField(
        max_length=128, blank=True, default="", db_index=True
    )

    is_synced = models.BooleanField(default=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_potholes",
    )

    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")

    points_awarded = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Pothole {self.id} ({self.region})"


# ────────────────────────────────────────────────────────────────
# Redemption / Airtime Requests
# ────────────────────────────────────────────────────────────────
class RedemptionRequest(TimeStampedModel):
    from core.utils import generate_reference
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="redemptions",
    )

    points = models.PositiveIntegerField()
    airtime_amount = models.DecimalField(max_digits=6, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    mtn_phone = models.CharField(
        max_length=20,
        validators=[validate_ghana_phone],
    )

    reference = models.CharField(max_length=32, default=generate_reference, unique=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_redemptions",
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Redeem {self.user} {self.airtime_amount} ({self.status})"
