"""
Filename: urls.py
Path: src/config/urls.py
Description: Основные URL маршруты проекта с health check
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

# Import здесь чтобы не создавать отдельное приложение
from django.http import HttpResponse
from django.views import View

class HealthCheckView(View):
    """Simple health check"""
    def get(self, request):
        return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.tasks.urls')),
    path('users/', include('apps.users.urls')),
    path('api/templates/', include('apps.temp.urls')),

    # Health check
    path('health/', HealthCheckView.as_view(), name='health_check'),
]

# Раздача медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
