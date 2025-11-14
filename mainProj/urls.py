from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

from core.api import api as api_v1


# ------------------------------
# Healthcheck (for Render / Docker)
# ------------------------------
def healthcheck(request):
    return JsonResponse({"status": "ok"}, status=200)


urlpatterns = [
    # --- Admin ---
    path("admin/", admin.site.urls),

    # --- Health Check (very important for production) ---
    path("health/", healthcheck),

    # --- Versioned API ---
    path("api/v1/", api_v1.urls),
]


# -----------------------------------------------------
# MEDIA (only served by Django when DEBUG=True)
# In production, Nginx or CDN should serve media files.
# -----------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
