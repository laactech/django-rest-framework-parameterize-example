import uuid

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from . import exceptions, utils

User = get_user_model()

READ_ONLY_MODELS = (User,)


@pytest.mark.django_db
def test_api_requires_authentication(tp_api, all_url_name):
    kwargs = {"version": "v1"}
    if "detail" in all_url_name:
        kwargs["uuid"] = uuid.uuid4()
    reversed_url = reverse(
        f"api_root:{all_url_name}", current_app="api_root", kwargs=kwargs,
    )
    response = tp_api.client.get(reversed_url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_user_api_list_views_access(tp_api, user, list_view_info):
    reversed_url = reverse(
        f"api_root:{list_view_info.view_name}",
        current_app="api_root",
        kwargs={"version": "v1"},
    )
    tp_api.client.force_authenticate(user=user.user)
    response = tp_api.client.get(reversed_url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_api_detail_views_access(tp_api, user, detail_view_info, factory_classes):
    factory_cls, viewset_class = utils.get_matching_factory_class(
        factory_classes, detail_view_info.import_path
    )
    obj = utils.create_matching_object(factory_cls, user)
    reversed_url = reverse(
        f"api_root:{detail_view_info.view_name}",
        current_app="api_root",
        kwargs={"version": "v1", "uuid": obj.uuid},
    )
    tp_api.client.force_authenticate(user=user.user)
    response = tp_api.client.get(reversed_url)
    if not hasattr(viewset_class, "retrieve"):
        expected_status_code = 405
    else:
        expected_status_code = 200
    assert response.status_code == expected_status_code


@pytest.mark.django_db
def test_user_api_create_views_access(
    tp_api, user, list_view_info, api_version, factory_classes, viewset_detail_classes,
):
    try:
        factory_cls, viewset_class = utils.get_matching_factory_class(
            factory_classes, list_view_info.import_path
        )
    except exceptions.NoSerializerClassFoundException:
        # If not serializer class is found, then we can't create a model to attempt a post
        return
    obj = utils.build_matching_object(
        factory_cls, user, api_version, viewset_detail_classes, factory_classes,
    )
    reversed_url = reverse(
        f"api_root:{list_view_info.view_name}",
        current_app="api_root",
        kwargs={"version": api_version},
    )
    tp_api.client.force_authenticate(user=user.user)
    response = tp_api.client.post(reversed_url, obj, format="json")
    if not hasattr(viewset_class, "perform_create"):
        expected_status_code = 405
    else:
        expected_status_code = 201
    assert response.status_code == expected_status_code


@pytest.mark.django_db
def test_user_api_detail_view_delete(
    tp_api, user, detail_view_info, api_version, factory_classes
):
    factory_cls, viewset_class = utils.get_matching_factory_class(
        factory_classes, detail_view_info.import_path
    )
    obj = utils.create_matching_object(factory_cls, user)
    reversed_url = reverse(
        f"api_root:{detail_view_info.view_name}",
        current_app="api_root",
        kwargs={"version": api_version, "uuid": obj.uuid},
    )
    tp_api.client.force_authenticate(user=user)
    response = tp_api.client.delete(reversed_url)
    if not hasattr(viewset_class, "perform_destroy"):
        expected_status_code = 405
    else:
        expected_status_code = 204
    assert response.status_code == expected_status_code
