from dataclasses import dataclass

from rest_framework.viewsets import GenericViewSet


@dataclass
class ViewInfo:
    view_name: str
    import_path: str

    def __str__(self):
        return f"{self.view_name} {self.import_path}"


@dataclass
class ViewsetClass:
    view_name: str
    class_: GenericViewSet
    import_path: str

    def __str__(self):
        return f"{self.view_name} {self.class_}"
