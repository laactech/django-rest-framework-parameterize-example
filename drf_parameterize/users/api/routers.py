from rest_framework.routers import DefaultRouter

from . import constants, viewsets

router = DefaultRouter()
router.root_view_name = "users_root"
router.register(r"users", viewsets.UserViewset, basename=constants.USER_BASENAME)
