from rest_framework.filters import BaseFilterBackend
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import mixins, views
from rest_framework.compat import coreapi, coreschema, distinct, guardian
from django.utils.encoding import force_text
from rest_framework.settings import api_settings
from Backend.extend.CustomRouter import MultipleEntranceRouter


class MultipleEntranceFilterBackend(BaseFilterBackend):
    """
    A base class from which all filter backend classes should inherit.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Return a filtered queryset.
        """
        foreign_lookup_field = getattr(view, 'foreign_lookup_field', None)
        assert foreign_lookup_field is not None, 'if you want to use MultipleEntranceFilerBackend, foreign_lookup_field should not be None, '
        for viewSet, k in foreign_lookup_field.items():
            k = MultipleEntranceRouter().get_nested_lookup_key(viewSet, k)
            v = view.kwargs.get(k, None)
            if v:
                queryset = queryset.filter(**{k: v})
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        return queryset

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name='foreign_lookup_field',
                required=False,
                location='path',
                schema=coreschema.String(
                    title=force_text("foreign look up "),
                    description=force_text("foreign look up ")
                )
            )
        ]
