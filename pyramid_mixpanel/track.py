"""Tracking user events and profiles."""

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
    profile_properties: ProfileProperties
    profile_meta_properties: ProfileMetaProperties

    @staticmethod
    def _resolve_events(dotted_name: t.Optional[object] = None) -> Events:
        """Resolve a dotted-name into an Events object and set it to self.events."""
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
                    f"class in dotted_name needs to be based on pyramid_mixpanel.Events"
                )
            return resolved()

    @staticmethod
    def _resolve_event_properties(
        dotted_name: t.Optional[object] = None
    ) -> EventProperties:
        """Resolve a dotted-name into an EventProperties object and set it to self.event_properties."""
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
                    f"class in dotted_name needs to be based on pyramid_mixpanel.EventProperties"
                )
            return resolved()

    @staticmethod
    def _resolve_profile_properties(
        dotted_name: t.Optional[object] = None
    ) -> ProfileProperties:
        """Resolve a dotted-name into an ProfileProperties object and set it to self.profile_properties."""
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
                    f"class in dotted_name needs to be based on pyramid_mixpanel.ProfileProperties"
                )
            return resolved()

    @staticmethod
    def _resolve_profile_meta_properties(
        dotted_name: t.Optional[object] = None
    ) -> ProfileMetaProperties:
        """Resolve a dotted-name into an ProfileMetaProperties object and set it to self.profile_meta_properties."""
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
                    f"class in dotted_name needs to be based on pyramid_mixpanel.ProfileMetaProperties"
                )
            return resolved()

    def __init__(self, settings: SettingsType, distinct_id=None) -> None:
        """Initialize API connector."""
        self.distinct_id = distinct_id

        if settings.get("mixpanel.token"):
            self.api = Mixpanel(
                token=settings["mixpanel.token"], consumer=PoliteBufferedConsumer()
            )
        else:
            self.api = Mixpanel(token="testing", consumer=MockedConsumer())  # nosec

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

    @distinct_id_is_required
    def track(self, event: Event, props: t.Optional[PropertiesType] = None) -> None:
        """Track a Mixpanel event."""
        if not props:
            props = {}

        if event not in self.events.__dict__.values():
            raise ValueError(f"Event '{event}' is not a member of self.events")

        for prop in props.keys():
            if prop not in self.event_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.event_properties"
                )

        self.api.track(
            self.distinct_id,
            event.name,
            {prop.name: value for (prop, value) in props.items()},
        )

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

        for prop in props.keys():
            if prop not in self.profile_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_properties"
                )

        for prop in meta.keys():
            if prop not in self.profile_meta_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_meta_properties"
                )

        self.api.people_set(
            self.distinct_id,
            {prop.name: value for (prop, value) in props.items()},
            {prop.name: value for (prop, value) in meta.items()},
        )

    @distinct_id_is_required
    def people_append(
        self, props: PropertiesType, meta: t.Optional[PropertiesType] = None
    ) -> None:
        """Wrap around api.people_append to set distinct_id."""
        if not meta:
            meta = {}

        for prop in props.keys():
            if prop not in self.profile_properties.__dict__.values():
                raise ValueError(
                    f"Property '{prop}' is not a member of self.profile_properties"
                )

        for prop in meta.keys():
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
    def profile_increment(self, props: t.Dict[Property, int]) -> None:
        """Wrap around api.people_increment to set distinct_id."""
        for prop in props.keys():
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

        for prop in props.keys():
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

    return MixpanelTrack(settings=request.registry.settings, distinct_id=distinct_id)


def mixpanel_flush(event: NewRequest) -> None:
    """Send out all pending messages on Pyramid request end."""

    def flush(request: Request, response: Response) -> None:
        """Send all the enqueued messages at the end of request lifecycle."""

        # If request.mixpanel was never called during request runtime, then
        # skip initializing and flushing MixpanelTrack.
        if "mixpanel" not in request.__dict__:
            return

        # Send all messages to Mixpanel for those consumers that require
        # manual flushing at the end of request life-cycle.
        if getattr(request.mixpanel.api._consumer, "flush", None):  # noqa: 236
            request.mixpanel.api._consumer.flush()

    event.request.add_response_callback(flush)
