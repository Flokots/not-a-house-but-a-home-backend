from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from nahbah.views import view_site_redirect


def health_check(request):
    return JsonResponse({"status": "healthy", "service": "Not A House But A Home API"})


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('api/', include('nahbah.urls')),  # Include the API URLs
    path('', view_site_redirect, name='view_site'),
]

# Serve media files during development
if settings.DEBUG:
    print(f"DEBUG: Adding media URL pattern for {settings.MEDIA_URL} -> {settings.MEDIA_ROOT}")
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)