"""The generated API documentation: what the schema says about the portal, and what it leaves out.

``describe_api`` is a drf-spectacular postprocessing hook named in
``SPECTACULAR_SETTINGS["POSTPROCESSING_HOOKS"]``. It appends to the schema's description how
to authenticate, the limits and the page sizes, read from the settings and the pagination
class at the moment the schema is generated, so the text cannot drift from what the portal does.
It also gives the schema one tagged section for each list the portal serves, and gives each
registered type's record the description its registration holds.
"""

from __future__ import annotations

import inspect
from typing import Any, cast

from drf_spectacular.contrib.django_filters import DjangoFilterExtension
from drf_spectacular.contrib.knox_auth_token import KnoxTokenScheme
from rest_framework.settings import api_settings


class ApiDescription:
    """The part of the schema's description that comes from the portal's settings."""

    def render(self) -> str:
        """Write the sections on authentication, limits and paging.

        Returns:
            Markdown that follows the description a portal writes.
        """
        return "\n\n".join((self.authentication(), self.limits(), self.paging()))

    def authentication(self) -> str:
        """Describe how a caller proves who they are.

        Returns:
            A Markdown section on tokens and sessions.
        """
        return (
            "### Authentication\n\n"
            "Most data can be read without signing in. To create, change or delete "
            "records, or to read records that are not public, identify yourself in one "
            "of two ways:\n\n"
            "- **Token**: create one on your account pages, under API tokens, and send it "
            "with every request as `Authorization: Token <your-token>`. A token is shown "
            "once, when it is created.\n"
            "- **Session**: a page that is part of the portal can call the API with the "
            "signed-in person's session, sending the CSRF token with each write."
        )

    def limits(self) -> str:
        """List the request limits as the settings hold them.

        Returns:
            A Markdown section with one line per configured rate, or an empty section
            when no rate is set.
        """
        rates = api_settings.DEFAULT_THROTTLE_RATES or {}
        lines = [f"- `{scope}`: {rate}" for scope, rate in rates.items() if rate]
        if not lines:
            return "### Limits\n\nThe portal sets no limit on requests."
        return (
            "### Limits\n\n"
            "A caller past a limit is answered `429` with a `Retry-After` header "
            "saying how long to wait.\n\n" + "\n".join(lines)
        )

    def paging(self) -> str:
        """State the default and the largest page size of a list.

        Returns:
            A Markdown section read from the configured pagination class, or one saying a list
            is not paged when the portal sets none.
        """
        pagination_class = cast("Any", api_settings.DEFAULT_PAGINATION_CLASS)
        if pagination_class is None:
            return "### Paging\n\nA list returns all its records in one response."
        pagination = pagination_class()
        return (
            "### Paging\n\n"
            f"A list returns {pagination.page_size} records a page unless "
            f"`{pagination.page_size_query_param}` asks for another number, up to "
            f"{pagination.max_page_size}. Follow `next` in the response to read the "
            f"following page."
        )


class TypeDescription:
    """What the registration of one sample or measurement type says about it.

    The generated documentation shows these words wherever it names the type: the operations,
    the section the type's operations are grouped in, and the description of its record.
    """

    def __init__(self, config: Any) -> None:
        """Hold the registration to describe.

        Args:
            config: The type's :class:`~fairdm.registry.ModelConfiguration`.
        """
        self.config = config
        self.model = config.model

    @property
    def name(self) -> str:
        """The type's plural name, as the registration gives it."""
        return str(self.model._meta.verbose_name_plural)

    @property
    def title(self) -> str:
        """The type's singular display name."""
        return str(self.model._meta.verbose_name)

    def summary(self) -> str:
        """Say what the type is.

        Returns:
            The registration's description, else the one in its metadata, else the model's
            docstring, else a plain sentence naming the type.
        """
        metadata = self.config.metadata
        if self.config.description:
            return str(self.config.description)
        if metadata and metadata.description:
            return str(metadata.description)
        return self.model.__doc__ or f"Endpoints for managing {self.name}."

    def details(self) -> str:
        """Credit the type's authority and citation, and list its keywords.

        Returns:
            Markdown paragraphs for what the registration gives. A maintainer's name and email
            address are never part of it.
        """
        metadata = self.config.metadata
        if metadata is None:
            return ""
        paragraphs = []
        if metadata.authority:
            authority = metadata.authority
            name = str(authority.name)
            if authority.short_name:
                name += f" ({authority.short_name})"
            paragraphs.append(
                "**Authority:** " + ", ".join(filter(None, (name, authority.website)))
            )
        if metadata.citation:
            doi = f"DOI: {metadata.citation.doi}" if metadata.citation.doi else ""
            citation = " ".join(filter(None, (metadata.citation.text, doi)))
            if citation:
                paragraphs.append(f"**Citation:** {citation}")
        if metadata.keywords:
            keywords = ", ".join(str(word) for word in metadata.keywords)
            paragraphs.append(f"**Keywords:** {keywords}")
        return "\n\n".join(paragraphs)

    def tag(self) -> dict[str, Any]:
        """Describe the section of the documentation that groups the type's operations.

        Returns:
            An OpenAPI tag object, linking to the repository where the registration gives one.
        """
        description = "\n\n".join(filter(None, (self.summary(), self.details())))
        tag: dict[str, Any] = {"name": self.name, "description": description}
        metadata = self.config.metadata
        if metadata and metadata.repository_url:
            tag["externalDocs"] = {
                "url": metadata.repository_url,
                "description": "Repository",
            }
        return tag

    def component_names(self) -> tuple[str, str]:
        """Name the schema components that hold the type's record.

        Returns:
            The component drf-spectacular builds from the serializer, and its patched variant.
        """
        serializer = self.config.get_serializer_class()
        meta = getattr(serializer, "Meta", None)
        name = getattr(meta, "ref_name", None) or serializer.__name__.removesuffix(
            "Serializer"
        )
        return name, f"Patched{name}"


class TypeDocumentation:
    """The sections of the generated documentation, one for each list the portal serves."""

    def tags(self) -> list[dict[str, Any]]:
        """List a section for each core list, custom viewset and registered type.

        Returns:
            OpenAPI tag objects. A viewset on the router that is not generated from a
            registration is described by its own docstring.
        """
        from fairdm.api.router import fairdm_api_router

        tags: dict[str, dict[str, Any]] = {}
        for prefix, viewset, _basename in fairdm_api_router.registry:
            registration = getattr(viewset, "registration", None)
            if registration is not None:
                tag = TypeDescription(registration).tag()
            else:
                tag = {"name": prefix.split("/")[0]}
                own = viewset.__dict__.get("__doc__")
                if own:
                    tag["description"] = inspect.cleandoc(own)
            tags.setdefault(tag["name"], tag)
        return list(tags.values())

    def describe_records(self, components: dict[str, Any]) -> None:
        """Replace each registered type's record description with the type's own.

        Args:
            components: The schema's ``components.schemas``, changed in place.
        """
        from fairdm.registry import registry

        for model in (*registry.samples, *registry.measurements):
            description = TypeDescription(registry.get_for_model(model))
            for name in description.component_names():
                if name in components:
                    components[name]["title"] = description.title
                    components[name]["description"] = description.summary()


def describe_api(result: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Describe the portal in the schema: its limits, a section for each list and each type.

    Args:
        result: The generated schema.
        **kwargs: The generator, request and ``public`` flag drf-spectacular passes to a hook.

    Returns:
        The schema, with its ``info.description`` extended, a top-level ``tags`` list, and
        each registered type's record described by its registration.
    """
    info = result.setdefault("info", {})
    written = info.get("description", "").rstrip()
    info["description"] = "\n\n".join(
        filter(None, (written, ApiDescription().render()))
    )
    documentation = TypeDocumentation()
    result["tags"] = documentation.tags()
    documentation.describe_records(result.get("components", {}).get("schemas", {}))
    return result


class FairDMFilterExtension(DjangoFilterExtension):
    """Describe a list's filters as the API applies them.

    A filter on a relation that has no short identifier is removed when the filter set is
    built for a request, so the schema leaves it out too.
    """

    target_class = "fairdm.api.filters.FairDMFilterBackend"
    # Ahead of the extension for django-filter, which also matches this backend.
    priority = 1

    def resolve_filter_field(
        self, auto_schema, model, filterset_class, field_name, filter_field
    ):
        """Describe a filter unless the API drops it when it builds the filter set."""
        drops = getattr(filterset_class, "drops", None)
        if drops is not None and drops(filter_field):
            return []
        return super().resolve_filter_field(
            auto_schema, model, filterset_class, field_name, filter_field
        )


class TokenSchemeExtension(KnoxTokenScheme):
    """Describe the token header under a name a reader of the documentation understands."""

    # Ahead of the extension drf-spectacular ships for the same class.
    priority = 1
    name = "tokenAuth"

    def get_security_definition(self, auto_schema):
        """Add a plain description to the header scheme drf-spectacular builds.

        Args:
            auto_schema: The schema generator's view of the operation.

        Returns:
            The scheme as an OpenAPI security scheme object.
        """
        definition = super().get_security_definition(auto_schema)
        definition["description"] = (
            "A token created on your account pages, sent with every request as "
            "`Authorization: Token <token>`."
        )
        return definition
