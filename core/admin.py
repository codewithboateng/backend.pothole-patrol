from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
import csv

from .models import UserProfile, PotholeReport, RedemptionRequest
from .utils import award_report_points, send_airtime_to_user


# -------------------------------------------------------------------
# USER PROFILE ADMIN
# -------------------------------------------------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "points", "is_verified", "created_at")
    search_fields = ("user__username", "phone")


# -------------------------------------------------------------------
# CSV EXPORT ACTION
# -------------------------------------------------------------------
@admin.action(description="Export selected reports to CSV")
def export_reports_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="pothole_reports.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "id",
        "user",
        "region",
        "lat",
        "lng",
        "severity",
        "ai_valid",
        "ai_score",
        "status",
        "is_spam",
        "points_awarded",
        "submitted_ip",
        "device_id",
        "created_at",
        "approved_at",
    ])

    for r in queryset:
        writer.writerow([
            str(r.id),
            r.user.username if r.user else "",
            r.region,
            r.latitude,
            r.longitude,
            r.severity,
            r.ai_valid,
            r.ai_score,
            r.status,
            r.is_spam,
            r.points_awarded,
            r.submitted_ip,
            r.device_id,
            r.created_at.isoformat(),
            r.approved_at.isoformat() if r.approved_at else "",
        ])

    return response


# -------------------------------------------------------------------
# APPROVE REPORT ACTION (Uses award_report_points)
# -------------------------------------------------------------------
@admin.action(description="Approve selected pothole reports")
def approve_reports(modeladmin, request, queryset):
    admin_user = request.user

    for report in queryset:
        # Only pending reports can be approved
        if report.status != PotholeReport.Status.PENDING:
            continue

        # Reject invalid images
        if not report.ai_valid:
            report.status = PotholeReport.Status.REJECTED
            report.rejection_reason = "AI rejected this image as non-pothole."
            report.save()
            continue

        # Mark approved
        report.status = PotholeReport.Status.APPROVED
        report.approved_at = timezone.now()
        report.approved_by = admin_user
        report.save()

        # Award points through helper
        award_report_points(report)

    modeladmin.message_user(
        request,
        "Approved selected reports. Points awarded via award_report_points()."
    )


# -------------------------------------------------------------------
# REJECT REPORT ACTION
# -------------------------------------------------------------------
@admin.action(description="Reject selected pothole reports")
def reject_reports(modeladmin, request, queryset):
    for report in queryset:
        report.status = PotholeReport.Status.REJECTED
        if not report.rejection_reason:
            report.rejection_reason = "Rejected by admin."
        report.save()

    modeladmin.message_user(request, "Selected reports rejected.")


# -------------------------------------------------------------------
# POTHOLE REPORT ADMIN
# -------------------------------------------------------------------
@admin.register(PotholeReport)
class PotholeReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "region",
        "severity",
        "ai_valid",
        "is_spam",
        "status",
        "points_awarded",
        "created_at",
    )
    list_filter = ("region", "status", "is_spam", "ai_valid")
    search_fields = ("user__username", "region", "device_id", "submitted_ip")
    actions = [approve_reports, reject_reports, export_reports_csv]


# -------------------------------------------------------------------
# APPROVE REDEMPTION REQUEST (Uses send_airtime_to_user)
# -------------------------------------------------------------------
@admin.action(description="Approve MTN airtime redemption")
def approve_redemption(modeladmin, request, queryset):
    admin_user = request.user

    for redemption in queryset:
        if redemption.status != RedemptionRequest.Status.PENDING:
            continue

        success, reference = send_airtime_to_user(
            phone=redemption.mtn_phone,
            amount=float(redemption.airtime_amount),
        )

        if success:
            redemption.status = RedemptionRequest.Status.APPROVED
            redemption.reference = reference
            redemption.approved_by = admin_user
            redemption.approved_at = timezone.now()

            # Safe point deduction
            profile = redemption.user.profile
            profile.points = max(0, profile.points - redemption.points)
            profile.save()

        else:
            redemption.status = RedemptionRequest.Status.REJECTED
            redemption.rejection_reason = "Airtime API error. Try again."

        redemption.save()

    modeladmin.message_user(request, "Redemption requests processed.")


# -------------------------------------------------------------------
# REDEMPTION ADMIN
# -------------------------------------------------------------------
@admin.register(RedemptionRequest)
class RedemptionRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "points",
        "airtime_amount",
        "mtn_phone",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("user__username", "mtn_phone")
    actions = [approve_redemption]
