"""
URL configuration for CategoryTree project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, \
    SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('category.urls')),
    path('api/schema/', SpectacularAPIView.as_view(),
         name='schema'),
    path('api/docs/',
         SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/redoc/',
         SpectacularRedocView.as_view(url_name='schema'))
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Adding this static media url only for the purposes of the task. It should
# not be done so in production as it is a serious security risk. There it
# should be best practice to use s3 or azure.
