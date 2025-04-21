from decouple import config
from django.urls import include, path
from drf_yasg.openapi import Contact, Info, License
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

schema_view = get_schema_view(
    info=Info(
        title='Banking API',
        default_version='v1',
        description='API for managing loans and loan payments',
        terms_of_service='https://www.google.com/policies/terms/',
        contact=Contact(email=config('CONTACT_EMAIL')),
        license=License(name='BSD License'),
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(permission_classes=[AllowAny]), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(permission_classes=[AllowAny]), name='token_refresh'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', include('django_prometheus.urls')),
    path('banking/', include('banking.api.urls')),
]
