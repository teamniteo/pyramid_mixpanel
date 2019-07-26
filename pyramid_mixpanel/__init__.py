"""Integration with Mixpanel.

There are two things you can do:
* Send user interaction events or set profile properties via MixpanelTrack.
* Query for events and profiles via MixpanelQuery.

MixpanelTrack is prepared as `request.mixpanel` for easier usage in view code.
"""
from dataclasses import dataclass
from dataclasses import field
from mixpanel import Mixpanel
from pyramid.config import Configurator
from pyramid.path import DottedNameResolver
from pyramid.request import Request

import json
import requests
import structlog
import typing as t

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class Event:
    """A single event that we send to Mixpanel."""

    # The name of this event that will be shown in Mixpanel. Should be
    # something nice, like "Page Viewed".
    name: str


@dataclass(frozen=True)
class Events:
    """Let's be precise which events we will send.

    Otherwise different parts of code will send slightly differently named
    events and then you can wish good luck to the marketing/product team
    when they are trying to decipher what's the difference between
    "Page Load", "User Visited" and "Viewed Page".

    So we're only allowing properties listed below. You can provide your own
    list of properties via the `mixpanel.events` setting.
    """

    # Any page view should be tracked with this event. More specific events
    # can then be built with Mixpanel Web UI by filtering these events by
    # path and/or title. Further info:
    # https://help.mixpanel.com/hc/en-us/articles/115004562246-Combine-Events-To-Create-A-Custom-Event
    page_viewed: Event = Event("Page Viewed")

    # Any click should be tracked with this event. More specific events
    # can then be built with Mixpanel Web UI by filtering these events by
    # path and/or title. Further info:
    # https://help.mixpanel.com/hc/en-us/articles/115004562246-Combine-Events-To-Create-A-Custom-Event
    button_link_clicked: Event = Event("Button/Link Clicked")

    # Events for tracking user's account/subscription status.
    user_signed_up: Event = Event("User Signed Up")
    user_logged_in: Event = Event("User Logged In")
    user_charged: Event = Event("User Charged")
    user_disabled: Event = Event("User Disabled")


@dataclass(frozen=True)
class Property:
    """A single property that we attach to Mixpanel events or profiles."""

    # The name of this property that will be shown in Mixpanel. Should be
    # something nice, like "Path" or "Title". Some properties are ~special~
    # and they are prefixed with the dollar sign ($). Read more about them on
    # https://help.mixpanel.com/hc/en-us/articles/115004602703-Reserved-or-Special-Properties
    name: str


@dataclass(frozen=True)
class EventProperties:
    """Let's be precise which properties we will set on Events.

    Otherwise different parts of code will set slightly differently named
    properties and then you can wish good luck to the marketing/product team
    when they are trying to decipher what's the difference between "title" and
    "name".

    So we're only allowing properties listed below. You can provide your own
    list of properties via the `mixpanel.event_properties` setting.
    """

    # Used for building bespoke custom events from Page Viewed and
    # Button/Link Clicked events.
    title: Property = Property("Title")
    path: Property = Property("Path")

    # Referring URL, including your own domain.
    dollar_referrer: Property = Property("$referrer")


@dataclass(frozen=True)
class ProfileProperties:
    """Let's be precise which properties we will set on Profile records.

    Otherwise different parts of code will set slightly differently named
    properties and then you can wish good luck to the marketing/product team
    when they are trying to decipher what's the difference between "state" and
    "status".

    So we're only allowing properties listed below. You can provide your own
    list of properties via `mixpanel.profile_properties` setting.
    """

    # The time when the user created their account. This should be expressed
    # as a Mixpanel date string.
    dollar_created: Property = Property("$created")

    # The user's email address as a string, e.g. "joe.doe@example.com".
    # Mixpanel will use the "$email" property when sending email messages
    # to your users, and for displaying the user's gravatar image in reports.
    dollar_email: Property = Property("$email")

    # The users full name. If it is set, the full name of the user will be
    # displayed in Mixpanel reports, plus you can craft more personalized
    # automated email and in-app message.
    dollar_name: Property = Property("$name")

    # The user's phone number as a string, e.g. "4805551212". Mixpanel will
    # use the "$phone" property when sending SMS messages to your users.
    dollar_phone: Property = Property("$phone")

    # If this property is set to any value, a user will be unsubscribed
    # from Mixpanel automated email messages.
    dollar_unsubscribed: Property = Property("$unsubscribed")

    # State of user's account or subscription. Not something that Mixpanel
    # tracks by default, but pyramid_mixpanel expects to be tracked.
    state: Property = Property("State")


@dataclass(frozen=True)
class ProfileMetaProperties:
    """Warning: here be dragons! Overrides of how Mixpanel works.

    There are used very rarely to send special values to Mixpanel to override
    sane default behavior.
    """

    # The IP address associated with a given profile. Mixpanel uses IP for
    # geo-locating the profile. If $ip isn't provided the underlying library
    # will set it to 0, and Mixpanel will ignore it. You probably have Mixpanel
    # installed in the frontend, and that sends over user's real IP so you can
    # leave this one empty.
    dollar_ip: Property = Property("$ip")

    # Seconds since midnight, January 1st 1970, UTC. Updates are applied
    # in $time order, so setting this value can lead to unexpected results
    # unless care is taken. If $time isn't provided the underlying library
    # will set it to `time.time()`.
    dollar_time: Property = Property("$time")

    # If the $ignore_time property is present and true in your update request,
    # Mixpanel will not automatically update the "Last Seen" property of the
    # profile. Otherwise, Mixpanel will add a "Last Seen" property associated
    # with the current time for all $set, $append, and $add operations.
    dollar_ignore_time: Property = Property("$ignore_time")

    # If the $ignore_alias property is present and true in your update request,
    # Mixpanel will apply the update directly to the profile with the
    # distinct_id included in the request, rather than allowing this
    # distinct_id to be recognized as an alias during ingestion.
    dollar_ignore_alias: Property = Property("$ignore_alias")


SettingsType = t.Dict[str, t.Union[str, int, bool]]
PropertiesType = t.Dict[Property, t.Union[str, int, bool]]

#################################################
#              ---- Tracking ----               #
# Utilities for tracking user actions handlers. #
#################################################


class MixpanelTrack:
    """Wrapper around the official `mixpanel` server-side integration of Mixpanel.

    You can track events and/or set people profiles. Uses
    https://pypi.python.org/pypi/mixpanel under the hood.
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

    # TODO: Add typing for user, possibly with
    # https://mypy.readthedocs.io/en/latest/protocols.html#simple-user-defined-protocols
    def __init__(self, user, settings: SettingsType) -> None:
        """Initialize API connector."""
        self.user = user

        if settings.get("mixpanel.testing"):
            self.api = Mixpanel(token="testing", consumer=MockedConsumer())  # nosec
        else:
            self.api = Mixpanel(
                token=settings["mixpanel.token"], consumer=QueuedConsumer()
            )

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

    # TODO: decorator that verifies that events are enums and not strings
    # TODO: Can event_name be an Enum object instead of a string?

    def track(self, event: Event, props: t.Optional[PropertiesType] = None) -> None:
        """Track a Mixpanel event."""
        if not props:
            props = {}

        # TODO: event should be member of self.events

        self.api.track(
            self.user.distinct_id,
            event.name,
            {prop.name: value for (prop, value) in props.items()},
        )

    def profile_sync(
        self,
        extra: t.Optional[PropertiesType] = None,
        meta: t.Optional[PropertiesType] = None,
    ) -> None:
        """Create or update user's Profile.

        The `meta` argument overrides Mixpanel special properties, such as $ip.
        """
        props = {
            # fmt: off
            self.profile_properties.dollar_email: self.user.email,
            self.profile_properties.dollar_created: self.user.created.isoformat(),
            self.profile_properties.state: self.user.state,
            # fmt: on
        }
        if extra:
            props.update(extra)

        self.profile_set(props, meta=meta)

    def profile_set(
        self, props: PropertiesType, meta: t.Optional[PropertiesType] = None
    ) -> None:
        """Set properties to a Profile.

        This creates a profile if one does not yet exist.

        Use `meta` to override are Mixpanel special properties, such as $ip.
        """
        if not meta:
            meta = {}

        # TODO: props items should be members of self.profile_properties

        self.api.people_set(
            self.user.distinct_id,
            {prop.name: value for (prop, value) in props.items()},
            {prop.name: value for (prop, value) in meta.items()},
        )

    def profile_increment(self, props: t.Dict[Property, int]) -> None:
        """Wrap around api.people_increment to set distinct_id."""
        self.api.people_increment(
            self.user.distinct_id, {prop.name: value for (prop, value) in props.items()}
        )

    def profile_track_charge(
        self, amount: int, props: t.Optional[t.Dict[Property, str]] = None
    ) -> None:
        """Wrap around api.people_track_charge to set distinct_id."""
        if not props:
            props = {}

        self.api.people_track_charge(
            self.user.distinct_id,
            amount,
            {prop.name: value for (prop, value) in props.items()},
        )


@dataclass(frozen=True)
class QueuedConsumer:
    """Queue sending Mixpanel messages in a separate background queue processor."""

    def send(self, endpoint, json_message):
        """Queue sending of Mixpanel message in a background task."""
        # send_api.delay(endpoint, json_message)
        raise NotImplementedError


@dataclass(frozen=True)
class MockedMessage:
    """A single Mixpanel message stored by MockedConsumer."""

    endpoint: str
    msg: t.Dict["str", object]


@dataclass(frozen=True)
class MockedConsumer:
    """Save messages in an internal list, useful in unit testing."""

    # Internal storage of mocked message
    mocked_messages: t.List = field(default_factory=lambda: [])

    def send(self, endpoint, json_message):
        """Append message to the mocked_messages list."""
        msg = MockedMessage(endpoint=endpoint, msg=json.loads(json_message))
        self.mocked_messages.append(msg)


def mixpanel_track(request: Request):
    """Return MixpanelTrack class instance."""
    return MixpanelTrack(settings=request.registry.settings, user=request.user)


def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    config.add_request_method(mixpanel_track, "mixpanel", reify=True)


##############################################
#          ---- Data Querying ----           #
# Utilities for querying data from Mixpanel. #
##############################################


class MixpanelQuery(object):
    """Query Mixpanel for events and profiles.

    You can use one of the pre-built queries, or provide your own.
    """

    ENDPOINT = "https://mixpanel.com/api/2.0/jql"

    def __init__(self, settings: t.Dict[str, str]) -> None:
        """Save API credentials."""
        self.api_secret = settings["mixpanel.api_secret"]

    def jql(self, jql: str) -> t.List[t.Dict]:
        """Query Mixpanel using JQL script.

        You can troubleshoot the script on
        https://mixpanel.com/report/<PROJECT_ID>/jql-console.
        """
        resp = requests.post(
            self.ENDPOINT, auth=(self.api_secret, ""), data={"script": jql}
        )
        resp.raise_for_status()
        return resp.json()

    #################################################
    #         ---- Pre-built queries ----           #
    # A couple of queries that we use all the time. #
    #################################################

    def profile_by_email(self, email: str):
        """Return a Mixpanel profile by given email."""
        profiles = self.jql(
            """
            function main() {
              return People(
              )
              .filter(function(profile) {
                return profile.properties.$email == '%(email)s';
              })
              .map(function(profile) {
                return {
                  distinct_id: profile.distinct_id,
                  email: profile.properties.$email,
                };
              });
            }
        """
            % {"email": email}
        )

        if len(profiles) == 0:
            return None
        elif len(profiles) == 1:
            return profiles[0]
        else:
            raise ValueError(
                f"Found more than one Profile for email '{email}': "
                f"{[profile['distinct_id'] for profile in profiles]}"
            )
