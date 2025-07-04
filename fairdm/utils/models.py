from django.utils.decorators import classonlymethod

# from polymorphic.showfields import ShowFieldType
from fairdm.utils.utils import get_inheritance_chain


# class PolymorphicMixin(ShowFieldType):
class PolymorphicMixin:
    @classonlymethod
    def get_inheritance_chain(cls):
        return get_inheritance_chain(cls, cls.type_of)
