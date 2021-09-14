"""Integration with Mixpanel.

There are two things you can do:
* Send user interaction events or set profile properties via
  track.MixpanelTrack().
* Query for events and profiles via query.MixpanelQuery().

MixpanelTrack is prepared as `request.mixpanel` for easier usage in view code.
"""
from dataclasses import dataclass
from pyramid.config import Configurator
from pyramid.events import NewRequest


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

    So we're only allowing events listed below. You can provide your own
    list of events via the `mixpanel.events` setting.
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


def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    from pyramid_mixpanel.consumer import MockedConsumer
    from pyramid_mixpanel.track import mixpanel_flush
    from pyramid_mixpanel.track import mixpanel_init
    from pyramid_mixpanel.track import MixpanelTrack

    mixpanel = MixpanelTrack(settings=config.registry.settings)
    if config.registry.settings.get("pyramid_heroku.structlog"):
        import structlog

        logger = structlog.get_logger(__name__)
        logger.info(
            "Mixpanel configured",
            consumer=mixpanel.api._consumer.__class__.__name__,
            events=mixpanel.events.__class__.__name__,
            event_properties=mixpanel.event_properties.__class__.__name__,
            profile_properties=mixpanel.profile_properties.__class__.__name__,
            profile_meta_properties=mixpanel.profile_meta_properties.__class__.__name__,
            customerio=True if mixpanel.cio else False,
        )
        if mixpanel.api._consumer.__class__ == MockedConsumer:
            logger.warning("Mixpanel is in testing mode, no message will be sent!")

    else:
        import logging

        logger = logging.getLogger(__name__)

        logger.info(
            "Mixpanel configured "
            f"consumer={mixpanel.api._consumer.__class__.__name__}, "
            f"events={mixpanel.events.__class__.__name__}, "
            f"event_properties={mixpanel.event_properties.__class__.__name__}, "
            f"profile_properties={mixpanel.profile_properties.__class__.__name__}, "
            f"profile_meta_properties={mixpanel.profile_meta_properties.__class__.__name__}, "
            f"customerio={True if mixpanel.cio else False}"
        )
        if mixpanel.api._consumer.__class__ == MockedConsumer:
            logger.warning("Mixpanel is in testing mode, no message will be sent!")

    config.add_request_method(mixpanel_init, "mixpanel", reify=True)
    config.add_subscriber(mixpanel_flush, NewRequest)
