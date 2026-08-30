from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from app.chat.views import ChatSessionViewSet
from app.docs.views import DocumentViewSet

router = routers.DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"chat", ChatSessionViewSet, basename="chat")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("api/v1/auth/", include("djoser.urls")),
    path("api/v1/auth/", include("djoser.urls.jwt")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]