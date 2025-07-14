# -*- coding: utf-8 -*-
"""
Custom filter backends for API schema generation compatibility.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.schemas.openapi import AutoSchema


class SchemaDjangoFilterBackend(DjangoFilterBackend):
    """
    Custom DjangoFilterBackend that provides schema operation parameters
    for compatibility with older DRF schema generation.
    """

    def get_schema_operation_parameters(self, view):
        """
        Generate schema parameters for filtering.
        This method was removed in newer django-filter versions but is expected by DRF.
        """
        try:
            filterset_class = self.get_filterset_class(view, view.get_queryset())
            if not filterset_class:
                return []

            parameters = []
            for field_name, field in filterset_class.base_filters.items():
                parameter = {
                    "name": field_name,
                    "required": False,
                    "in": "query",
                    "description": getattr(
                        field, "help_text", f"Filter by {field_name}"
                    ),
                    "schema": {
                        "type": "string",
                    },
                }
                parameters.append(parameter)

            return parameters
        except Exception:
            # If anything goes wrong, return empty list rather than failing
            return []
