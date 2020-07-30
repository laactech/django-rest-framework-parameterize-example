import importlib.util
import random
from copy import deepcopy
from importlib import import_module
from pathlib import Path
from typing import Generator, Tuple

import factory
from django.db import models
from django.db.models.fields.related_descriptors import ManyToManyDescriptor
from django.urls import URLResolver
from factory.base import FactoryMetaClass
from rest_framework.reverse import reverse
from rest_framework.viewsets import GenericViewSet

from drf_parameterize.users.api.constants import USER_VIEW_NAME
from drf_parameterize.users.models import User

from .dataclasses import ViewsetClass
from .exceptions import NoSerializerClassFoundException


def create_matching_object(
    factory_class: factory.django.DjangoModelFactory, user: User,
) -> models.Model:
    """
    To generically test the api, we need to be able to generically create database models.
    All of our database models exposed via API must have an organization foreign key, and
    this function uses that assumption to properly create an object using our factories.
    Some of our models have a user or users attached, and this function accounts for that
    as well.
    """
    # Handle special cases
    if factory_class._meta.model == User:
        obj = factory_class.create()
        return obj

    obj = factory_class.create()

    # Handle many to many generic cases
    if hasattr(factory_class._meta.model, "users"):
        obj.users.add(user)
    return obj


def build_matching_object(
    factory_class: factory.django.DjangoModelFactory,
    user: User,
    api_version: str,
    viewset_detail_classes: list,
    factory_classes: list,
) -> dict:
    """
    This function exists specifically for the generic POST object creation test. The
    factory can be built into a dictionary which gets passed via POST to test the creation
    of new database objects.

    Due to our use of HyperlinkedModelSerializers, creating nested objects requires
    passing a URL, any foreign key, many to many, or one to one relationship that exists
    on a model must be referenced via the related object's URL.
    """
    user_url = reverse(
        USER_VIEW_NAME, kwargs={"uuid": user.uuid, "version": api_version},
    )
    kwargs = {}
    obj_urls = {}
    if hasattr(factory_class._meta.model, "user"):
        kwargs.update({"user": user})
        obj_urls["user"] = user_url
    obj = factory.build(dict, FACTORY_CLASS=factory_class, **kwargs)
    obj.update(obj_urls)
    obj = add_many_to_many_objects(obj, factory_class)
    obj = create_nested_object_urls(
        obj, viewset_detail_classes, factory_classes, user, api_version
    )
    return obj


def add_many_to_many_objects(
    obj: dict, factory_class: factory.django.DjangoModelFactory
) -> dict:
    """
    This function exists to identify what fields on a model are ManyToManyFields.
    ManyToManyFields need to be handled differently than a ForeignKey or a OneToOneField.
    The ManyToMany needs to be a list of model URLs when submitting.
    """
    for key, value in factory_class._meta.model.__dict__.items():
        if not key.startswith("_") and isinstance(value, ManyToManyDescriptor):
            many_to_many = getattr(factory_class._meta.model, key)
            if many_to_many.reverse is False:
                obj[key] = [many_to_many.rel.model]
    return obj


def create_nested_object_urls(
    obj: dict,
    viewset_detail_classes: list,
    factory_classes: list,
    user: User,
    api_version: str,
) -> dict:
    """
    This function exists to change the generated objects from a factory dictionary into
    their URL representation. When using a factory to build objects as dictionaries, the
    related models are generated as regular django model objects. We can't pass those as
    JSON, and due to our use of HyperlinkedModelSerializers, the related objects must be
    represented by their URL.

    This function creates any related objects and replaces them in the dictionary with
    their URL representation.
    """
    for key, value in deepcopy(obj).items():
        # This case handles a single model needing to be created such as a OneToOneField
        # or a ForeignKey
        if isinstance(value, models.Model):
            if viewset := next(
                (
                    vs
                    for vs in viewset_detail_classes
                    if isinstance(value, vs.class_.serializer_class.Meta.model)
                ),
                None,
            ):
                obj[key] = create_model_url(viewset, factory_classes, user, api_version)
            else:
                del obj[key]
        # This case handles the ManyToManyField
        elif isinstance(value, list):
            if viewset := next(
                (
                    vs
                    for vs in viewset_detail_classes
                    if issubclass(value[0], vs.class_.serializer_class.Meta.model)
                ),
                None,
            ):
                obj[key] = []
                for _ in range(random.randint(1, 4)):
                    obj[key].append(
                        create_model_url(viewset, factory_classes, user, api_version)
                    )
            else:
                del obj[key]
    return obj


def create_model_url(
    viewset: ViewsetClass, factory_classes: list, user: User, api_version: str,
) -> str:
    """
    This function exists to create a new model and turn it into its hyperlinked
    representation.
    """
    factory_cls, _ = get_matching_factory_class(factory_classes, viewset.import_path)
    new_value = factory_cls.create()
    return reverse(
        f"api_root:{viewset.view_name}",
        kwargs={"uuid": new_value.uuid, "version": api_version},
    )


def get_matching_factory_class(
    factory_classes: list, import_path: str
) -> Tuple[factory.django.DjangoModelFactory, GenericViewSet]:
    """
    This functions exists as a generic way to get the object's factory.
    Specifically, it matches the factory meta class's model with the viewset serializer
    meta class's model to validate that the factory can create the proper model.
    """
    viewset_class = import_viewset_class(import_path)
    try:
        matching_factories = set(
            fac
            for fac in factory_classes
            if fac._meta.model == viewset_class.serializer_class.Meta.model
            and isinstance(fac, FactoryMetaClass)
        )
    except AttributeError:
        raise NoSerializerClassFoundException
    if len(matching_factories) > 1:
        raise Exception(f"Found more than one factory for viewset {import_path}")
    try:
        factory_match = matching_factories.pop()
    except KeyError:
        raise Exception(f"Could not find a factory for viewset {import_path}")
    return factory_match, viewset_class


def import_viewset_class(import_path: str) -> GenericViewSet:
    """
    This function provides a generic way to import a class given the class module's import
    path. This is used specifically to import the viewset of the proper model.
    """
    split_import_path = import_path.rsplit(".", 1)
    viewset_module = import_module(split_import_path[0])
    viewset_class = getattr(viewset_module, split_import_path[1], None)
    if viewset_class is None:
        raise Exception(
            f"Could not import viewset {split_import_path[1]} from module"
            f" {split_import_path[0]}"
        )
    else:
        return viewset_class


def flatten_urlpatterns(url_patterns: list) -> Generator:
    """
    This function produces a generator that flattens the urlpatterns list. Some of the
    objects in the root urlpatterns are URLResolvers which have their own sub
    url_patterns.
    """
    for obj in url_patterns:
        if isinstance(obj, URLResolver):
            yield from flatten_urlpatterns(obj.url_patterns)
        else:
            yield obj


def import_factories(base_path: Path, factory_file_name: str = "factories.py") -> list:
    """
    This function exists to make adding new tests easier. Instead of manually defining all
    the different factory classes to import, this function will import any factory file
    within the given path assuming it is called factories.py.
    """
    modules = []
    for path in base_path.rglob("*.py"):
        if path.name == factory_file_name:
            root_module_name = path.parent.parent.absolute().name
            app_module_name = path.parent.absolute().name
            spec = importlib.util.spec_from_file_location(
                f"{root_module_name}.{app_module_name}.factories", str(path)
            )
            factory_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(factory_module)
            modules.append(factory_module)
    return modules
