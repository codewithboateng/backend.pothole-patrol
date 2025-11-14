from ninja import Schema, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# -------------------------------------------------------------
# AUTH SCHEMAS
# -------------------------------------------------------------
class RegisterRequest(Schema):
    username: str = Field(..., example="amaghana")
    password: str = Field(..., example="strongPass123")
    phone: str = Field(..., example="0244123456")


class LoginRequest(Schema):
    username: str
    password: str


class AuthResponse(Schema):
    access: str
    refresh: str
    user_id: int
    username: str
    phone: str
    points: int
    is_verified: bool


# -------------------------------------------------------------
# USER PROFILE
# -------------------------------------------------------------
class UserProfileOut(Schema):
    user_id: int
    username: str
    phone: str
    points: int
    is_verified: bool
    id_document: Optional[str] = None


# -------------------------------------------------------------
# ID UPLOAD
# -------------------------------------------------------------
class IDUploadRequest(Schema):
    file_base64: str


class IDUploadResponse(Schema):
    message: str
    is_verified: bool
    id_document_url: str


# -------------------------------------------------------------
# POTHOLE REPORT SCHEMAS
# -------------------------------------------------------------
class ReportSubmitRequest(Schema):
    image_base64: str
    latitude: float
    longitude: float
    region: str
    severity: int
    device_id: Optional[str] = None


class ReportSubmitResponse(Schema):
    id: UUID
    status: str
    message: str


class PotholeReportOut(Schema):
    id: UUID
    user: Optional[str]   # username
    region: str
    latitude: float
    longitude: float
    severity: int
    ai_valid: bool
    ai_score: Optional[float]
    status: str
    is_spam: bool
    created_at: datetime
    points_awarded: int


class PotholeMapItem(Schema):
    id: UUID
    region: str
    latitude: float
    longitude: float
    severity: int
    created_at: datetime


# -------------------------------------------------------------
# REDEMPTION / REWARDS
# -------------------------------------------------------------
class RedeemRequest(Schema):
    points: int
    mtn_phone: str


class RedeemResponse(Schema):
    id: int
    status: str
    message: str


class RedemptionOut(Schema):
    id: int
    points: int
    airtime_amount: float
    status: str
    mtn_phone: str
    reference: Optional[str]
    created_at: datetime
    approved_at: Optional[datetime]


# -------------------------------------------------------------
# GENERAL RESPONSES
# -------------------------------------------------------------
class SuccessResponse(Schema):
    success: bool = True
    message: str


class ErrorResponse(Schema):
    success: bool = False
    message: str
