from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "drf_parameterize.users"
    verbose_name = "Users"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        try:
            from drf_parameterize import users  # noqa: F401
        except ImportError:
            pass
