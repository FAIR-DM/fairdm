from django.apps import apps
from django.db.models.base import Model as Model
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404

from fairdm.contrib import CORE_MAPPING

from .utils import follow, is_following, unfollow


def follow_unfollow(request, uuid):
    model_class = apps.get_model(CORE_MAPPING[uuid[0]])
    instance = get_object_or_404(model_class, uuid=uuid)
    is_following_obj = is_following(request.user, instance)

    if is_following_obj:
        unfollow(request.user, instance)
    else:
        follow(request.user, instance)
    return HttpResponse(status=200)
