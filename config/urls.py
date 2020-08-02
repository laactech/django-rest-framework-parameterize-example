from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from drf_parameterize.core.views import HomeView

root_router = DefaultRouter()
root_router.root_view_name = "api_root"

urlpatterns = [
    path("", HomeView.as_view(), name="index"),
    re_path(r"^api/(?P<version>(v1))/", include((root_router.urls, "api_root"))),
    path("admin/", admin.site.urls),
]
