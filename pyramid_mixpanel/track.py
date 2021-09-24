"""Tracking user events and profiles."""

from mixpanel import BufferedConsumer
from mixpanel import Consumer
from mixpanel import Mixpanel
from pyramid.events import NewRequest
from pyramid.path import DottedNameResolver
from pyramid.request import Request
from pyramid.response import Response
from pyramid_mixpanel import Event
from pyramid_mixpanel import EventProperties
from pyramid_mixpanel import Events
from pyramid_mixpanel import ProfileMetaProperties
from pyramid_mixpanel import ProfileProperties
from pyramid_mixpanel import Property
from pyramid_mixpanel.consumer import MockedConsumer
from pyramid_mixpanel.consumer import MockedMessage
from pyramid_mixpanel.consumer import PoliteBufferedConsumer

import typing as t

SettingsType = t.Dict[str, t.Union[str, int, bool]]
PropertiesType = t.Dict[Property, t.Union[str, int, bool]]


def distinct_id_is_required(function: t.Callable) -> t.Callable:
    """Raise AttributeError if self.distinct_id is not set on MixpanelTrack."""

    def wrapper(*args, **kwargs):
        self = args[0]
        if not self.distinct_id:
            raise AttributeError(
                "distinct_id must be set before you can send events or set properties"
            )
        return function(*args, **kwargs)

    return wrapper


class MixpanelTrack:
    """Wrapper around the official `mixpanel` server-side integration for Mixpanel.

    You can track events and/or set people profiles. Uses
    https://pypi.python.org/pypi/mixpanel under the hood.

    Prepared as `request.mixpanel` for easy handling.
    """

    events: Events
    event_properties: EventProperties
    global_event_props: PropertiesType
    profile_properties: ProfileProperties
    profile_meta_properties: ProfileMetaProperties

    @staticmethod
    def _resolve_events(dotted_name: t.Optional[object] = None) -> Events:
        """Resolve a dotted-name into an Events object."""
        if not dotted_name:
            return Events()
        if not isinstance(dotted_name, str):
            raise ValueError(
                f"dotted_name must be a string, but it is: {dotted_name.__class__.__name__}"
            )
        else:
            resolved = DottedNameResolver().resolve(dotted_name)
            if not issubclass(resolved, Events):
                raise ValueError(
                    "class in dotted_name needs to be based on pyramid_mixpanel.Events"
                )
            return resolved()

    @staticmethod
    def _resolve_event_properties(
        dotted_name: t.Optional[object] = None,
    ) -> EventProperties:
        """Resolve a dotted-name into an EventProperties object."""
        if not dotted_name:
            return EventProperties()
        if not isinstance(dotted_name, str):
            raise ValueError(
                f"dotted_name must be a string, but it is: {dotted_name.__class__.__name__}"
            )
        else:
            resolved = DottedNameResolver().resolve(dotted_name)
            if not issubclass(resolved, EventProperties):
                raise ValueError(
                    "class in dotted_name needs to be based on pyramid_mixpanel.EventProperties"
                )
            return resolved()

    @staticmethod
    def _resolve_profile_properties(
        dotted_name: t.Optional[object] = None,
    ) -> ProfileProperties:
        """Resolve a dotted-name into an ProfileProperties object."""
        if not dotted_name:
            return ProfileProperties()
        if not isinstance(dotted_name, str):
            raise ValueError(
                f"dotted_name must be a string, but it is: {dotted_name.__class__.__name__}"
            )
        else:
            resolved = DottedNameResolver().resolve(dotted_name)
            if not issubclass(resolved, ProfileProperties):
                raise ValueError(
                    "class in dotted_name needs to be based on pyramid_mixpanel.ProfileProperties"
                )
            return resolved()

    @staticmethod
    def _resolve_profile_meta_properties(
        dotted_name: t.Optional[object] = None,
    ) -> ProfileMetaProperties:
        """Resolve a dotted-name into an ProfileMetaProperties object."""
        if not dotted_name:
            return ProfileMetaProperties()
        if not isinstance(dotted_name, str):
            raise ValueError(
                f"dotted_name must be a string, but it is: {dotted_name.__class__.__name__}"
            )
        else:
            resolved = DottedNameResolver().resolve(dotted_name)
            if not issubclass(resolved, ProfileMetaProperties):
                raise ValueError(
                    "class in dotted_name needs to be based on pyramid_mixpanel.ProfileMetaProperties"
                )
            return resolved()

    @staticmethod
    def _resolve_consumer(
        dotted_name: t.Optional[object] = None, use_structlog: t.Optional[bool] = False
    ) -> Consumer:
        """Resolve a dotted-name into a Consumer object."""
        if not dotted_name:
            return PoliteBufferedConsumer(use_structlog)
        if not isinstance(dotted_name, str):
            raise ValueError(
                f"dotted_name must be a string, but it is: {dotted_name.__class__.__name__}"
            )
        else:
            resolved = DottedNameResolver().resolve(dotted_name)
            if not (
                issubclass(resolved, Consumer) or issubclass(resolved, BufferedConsumer)
            ):
                raise ValueError(
                    "class in dotted_name needs to be based on mixpanel.(Buffered)Consumer"
                )
            return resolved()

    def __init__(
        self, settings: SettingsType, distinct_id=None, global_event_props=None
    ) -> None:
        """Initialize API connector."""
        self.distinct_id = distinct_id

        self.events = self._resolve_events(settings.get("mixpanel.events"))
        self.event_properties = self._resolve_event_properties(
            settings.get("mixpanel.event_properties")
        )
        self.profile_properties = self._resolve_profile_properties(
            settings.get("mixpanel.profile_properties")
        )
        self.profile_meta_properties = self._resolve_profile_meta_properties(
            settings.get("mixpanel.profile_meta_properties")
        )

        use_structlog = settings.get("pyramid_heroku.structlog", False) is True
        consumer = self._resolve_consumer(
            settings.get("mixpanel.consumer"), use_structlog
        )
        if settings.get("mixpanel.token"):
            self.api = Mixpanel(token=settings["mixpanel.token"], consumer=consumer)
        else:
            self.api = Mixpanel(token="testing", consumer=MockedConsumer())  # nosec

        if global_event_props:
            self.global_event_props = global_event_props
        else:
            self.global_event_props = {}

        if (
            settings.get("customerio.tracking.site_id")
            and settings.get("customerio.tracking.api_key")
            and settings.get("customerio.tracking.region")
        ):
            # This is here because customerio support is an install extra,
            # i.e. it is optional
            from customerio import CustomerIO
            from customerio import Regions

            if settings["customerio.tracking.region"] == "eu":
                region = Regions.EU
            elif settings["customerio.tracking.region"] == "us":
                region = Regions.US
            else:
                raise ValueError("Unknown customer.io region")

            self.cio = CustomerIO(
                settings["customerio.tracking.site_id"],
                settings["customerio.tracking.api_key"],
                region=region,
            )
        else:
            self.cio = None

    @distinct_id_is_required
    def track(self, event: Event, props: t.Optional[PropertiesType] = None) -> None:
        """Track a Mixpanel event."""
        if event not in self.events.__dict__.values():
            raise ValueError(f"Event '{event}' is not a member of self.events")

        if props:
            props = {**self.global_event_props, **props}
        else:
            props = self.global_event_props
        for prop in props:
            if prop not in self.event_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.event_properties"
                )

        self.api.track(
            self.distinct_id,
            event.name,
            {prop.name: value for (prop, value) in props.items()},
        )
        if self.cio:
            msg = {
                "customer_id": self.distinct_id,
                "name": event.name,
                **{
                    prop.name.replace("$", ""): value for (prop, value) in props.items()
                },
            }

            if self.api._consumer.__class__ == MockedConsumer:
                self.api._consumer.mocked_messages.append(
                    MockedMessage(endpoint="customer.io", msg=msg)
                )
            else:
                self.cio.track(**msg)

    @distinct_id_is_required
    def profile_set(
        self, props: PropertiesType, meta: t.Optional[PropertiesType] = None
    ) -> None:
        """Set properties to a Profile.

        This creates a profile if one does not yet exist.

        Use `meta` to override are Mixpanel special properties, such as $ip.
        """
        if not meta:
            meta = {}

        for prop in props:
            if prop not in self.profile_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_properties"
                )

        for prop in meta:
            if prop not in self.profile_meta_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_meta_properties"
                )

        self.api.people_set(
            self.distinct_id,
            {prop.name: value for (prop, value) in props.items()},
            {prop.name: value for (prop, value) in meta.items()},
        )
        if self.cio:
            msg = {
                "id": self.distinct_id,
                **{
                    prop.name.replace("$", ""): value for (prop, value) in props.items()
                },
                **{prop.name.replace("$", ""): value for (prop, value) in meta.items()},
            }

            if self.api._consumer.__class__ == MockedConsumer:
                self.api._consumer.mocked_messages.append(
                    MockedMessage(endpoint="customer.io", msg=msg)
                )
            else:
                self.cio.identify(**msg)

    @distinct_id_is_required
    def people_append(
        self, props: PropertiesType, meta: t.Optional[PropertiesType] = None
    ) -> None:
        """Wrap around api.people_append to set distinct_id."""
        if not meta:
            meta = {}

        for prop in props:
            if prop not in self.profile_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_properties"
                )

        for prop in meta:
            if prop not in self.profile_meta_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_meta_properties"
                )

        self.api.people_append(
            self.distinct_id,
            {prop.name: value for (prop, value) in props.items()},
            {prop.name: value for (prop, value) in meta.items()},
        )

    @distinct_id_is_required
    def people_union(
        self, props: PropertiesType, meta: t.Optional[PropertiesType] = None
    ) -> None:
        """Wrap around api.people_union to set properties."""
        if not meta:
            meta = {}

        for prop in props:
            if prop not in self.profile_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_properties"
                )
            if not isinstance(props[prop], list):
                raise TypeError(f"Property '{prop}' value is not a list")

        for prop in meta:
            if prop not in self.profile_meta_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_meta_properties"
                )
            if not isinstance(meta[prop], list):
                raise TypeError(f"Property '{prop}' value is not a list")

        self.api.people_union(
            self.distinct_id,
            {prop.name: value for (prop, value) in props.items()},
            {prop.name: value for (prop, value) in meta.items()},
        )

    @distinct_id_is_required
    def profile_increment(self, props: t.Dict[Property, int]) -> None:
        """Wrap around api.people_increment to set distinct_id."""
        for prop in props:
            if prop not in self.profile_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_properties"
                )

        self.api.people_increment(
            self.distinct_id, {prop.name: value for (prop, value) in props.items()}
        )

    @distinct_id_is_required
    def profile_track_charge(
        self, amount: int, props: t.Optional[t.Dict[Property, str]] = None
    ) -> None:
        """Wrap around api.people_track_charge to set distinct_id."""
        if not props:
            props = {}

        for prop in props:
            if prop not in self.profile_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_properties"
                )

        self.api.people_track_charge(
            self.distinct_id,
            amount,
            {prop.name: value for (prop, value) in props.items()},
        )


def mixpanel_init(request: Request) -> MixpanelTrack:
    """Return a configured MixpanelTrack class instance."""
    distinct_id = None
    if getattr(request, "user", None):
        distinct_id = request.user.distinct_id

    mixpanel = MixpanelTrack(
        settings=request.registry.settings, distinct_id=distinct_id
    )

    # Global event properties can be set from HTTP headers using
    # `X-Mixpanel-` prefix.
    #
    # Request with `X-Mixpanel-Foo: bar` header will set
    # `Foo` property for all events tracked in the lifetime of the request.
    event_props_from_header = {}
    for header in request.headers:
        if header.startswith("X-Mixpanel-"):
            property_name = header.replace("X-Mixpanel-", "").lower()
            event_prop = getattr(mixpanel.event_properties, property_name, None)
            if event_prop is not None:
                event_props_from_header[event_prop] = request.headers[header]
            else:
                if request.registry.settings.get("pyramid_heroku.structlog"):
                    import structlog

                    logger = structlog.get_logger(__name__)
                    logger.warning(
                        f"Property '{property_name}', from request header '{header}'"
                        " is not a member of event_properties"
                    )
                else:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Property '{property_name}', from request header '{header}'"
                        " is not a member of event_properties"
                    )
    mixpanel.global_event_props = event_props_from_header

    return mixpanel


def mixpanel_flush(event: NewRequest) -> None:
    """Send out all pending messages on Pyramid request end."""

    def flush(request: Request, response: Response) -> None:
        """Send all the enqueued messages at the end of request lifecycle."""

        # If request.mixpanel was never called during request runtime, then
        # skip initializing and flushing MixpanelTrack.
        if "mixpanel" not in request.__dict__:
            return

        request.mixpanel.api._consumer.flush()

    event.request.add_response_callback(flush)
