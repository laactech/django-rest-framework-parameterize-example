import inspect
import itertools
from pathlib import Path
from typing import List

import pytest

from config.urls import urlpatterns
from drf_parameterize.users.factories import UserFactory
from drf_parameterize.users.models import User

from .dataclasses import ViewInfo, ViewsetClass
from .utils import import_factories, import_viewset_class

"""
This gets all the URL patterns from the api root and puts them into a flat list using
the app name of the api root to filter. This ensures any time an api endpoint is added
it gets picked up by the tests. At the moment, I'm not sure of a better way to do this.
"""
api_root_url_patterns = list(
    itertools.chain.from_iterable(
        [
            path.url_patterns
            for path in urlpatterns
            if getattr(path, "app_name", "") == "api_root"
        ]
    )
)
api_root_list_url_patterns = [
    path for path in api_root_url_patterns if "list" in path.pattern.name
]
api_root_detail_url_patterns = [
    path for path in api_root_url_patterns if "detail" in path.pattern.name
]


@pytest.fixture(params=api_root_url_patterns)
def all_url_name(request) -> str:
    return request.param.pattern.name


@pytest.fixture(params=api_root_list_url_patterns)
def list_view_info(request) -> ViewInfo:
    return ViewInfo(
        view_name=request.param.pattern.name, import_path=request.param.lookup_str
    )


@pytest.fixture(params=api_root_detail_url_patterns)
def detail_view_info(request) -> ViewInfo:
    return ViewInfo(
        view_name=request.param.pattern.name, import_path=request.param.lookup_str
    )


@pytest.fixture
def user(db) -> User:
    return UserFactory.create()


@pytest.fixture(scope="session")
def factory_classes() -> list:
    factory_modules = import_factories(Path(__file__).parent.parent.absolute())
    factory_cls = []
    found_models = []
    for fac in factory_modules:
        for _, cls in fac.__dict__.items():
            if inspect.isclass(cls) and hasattr(cls, "_meta"):
                if hasattr(cls._meta, "model") and cls._meta.model not in found_models:
                    factory_cls.append(cls)
                    found_models.append(cls._meta.model)
    return factory_cls


@pytest.fixture(scope="session")
def viewset_detail_classes() -> List[ViewsetClass]:
    vs_classes = []
    for path in api_root_url_patterns:
        if "detail" in path.pattern.name:
            class_ = import_viewset_class(path.lookup_str)
            vs_classes.append(ViewsetClass(path.pattern.name, class_, path.lookup_str))
    return vs_classes
