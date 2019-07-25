"""Tests for Mixpanel tracking."""

from dataclasses import dataclass
from freezegun import freeze_time
from pyramid_mixpanel import Event
from pyramid_mixpanel import EventProperties
from pyramid_mixpanel import Events
from pyramid_mixpanel import MixpanelTrack
from pyramid_mixpanel import MockedConsumer
from pyramid_mixpanel import ProfileMetaProperties
from pyramid_mixpanel import ProfileProperties
from pyramid_mixpanel import Property
from pyramid_mixpanel import QueuedConsumer
from unittest import mock

# import mixpanel
import pytest


def _make_user(distinct_id="distinct id"):
    user = mock.Mock(spec="distinct_id".split())
    user.distinct_id = distinct_id
    return user


def test_init_consumers():
    """Test initialization of Consumer."""
    user = _make_user()

    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.token": "secret"})
    assert mixpanel.user == user
    assert mixpanel.api._consumer.__class__ == QueuedConsumer

    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.testing": True})
    assert mixpanel.user == user
    assert mixpanel.api._consumer.__class__ == MockedConsumer


@dataclass(frozen=True)
class FooEvents(Events):
    foo: Event = Event("Foo")


@dataclass(frozen=True)
class BarEvents:
    bar: Event = Event("Bar")


def test_init_events():
    """Test initialization of self.events."""
    user = _make_user()

    # default Events
    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.testing": True})
    assert mixpanel.events == Events()

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        user=user,
        settings={
            "mixpanel.testing": True,
            "mixpanel.events": "pyramid_mixpanel.tests.test_track.FooEvents",
        },
    )
    assert mixpanel.events == FooEvents()

    # the resolved Events need to be based off of pyramid_mixpanel.Events
    # to contain the events that this library expects
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            user=user,
            settings={
                "mixpanel.testing": True,
                "mixpanel.events": "pyramid_mixpanel.tests.test_track.BarEvents",
            },
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on pyramid_mixpanel.Events"
    )

    # passing Events as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            user=user,
            settings={  # type: ignore
                "mixpanel.testing": True,
                "mixpanel.events": FooEvents(),
            },
        )
    assert str(exc.value) == "dotted_name must be a string, but it is: FooEvents"


class FooEventProperties(EventProperties):
    foo: Property = Property("Foo")


@dataclass(frozen=True)
class BarEventProperties:
    bar: Property = Property("Bar")


def test_init_event_properties():
    """Test initialization of self.event_properties."""
    user = _make_user()

    # default EventProperties
    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.testing": True})
    assert mixpanel.event_properties == EventProperties()

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        user=user,
        settings={
            "mixpanel.testing": True,
            "mixpanel.event_properties": "pyramid_mixpanel.tests.test_track.FooEventProperties",
        },
    )
    assert mixpanel.event_properties == FooEventProperties()

    # the resolved EventProperties need to be based off of
    # pyramid_mixpanel.EventProperties to contain the event properties
    # that this library expects
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            user=user,
            settings={
                "mixpanel.testing": True,
                "mixpanel.event_properties": "pyramid_mixpanel.tests.test_track.BarEventProperties",
            },
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on pyramid_mixpanel.EventProperties"
    )

    # passing EventProperties as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            user=user,
            settings={  # type: ignore
                "mixpanel.testing": True,
                "mixpanel.event_properties": FooEventProperties(),
            },
        )
    assert (
        str(exc.value) == "dotted_name must be a string, but it is: FooEventProperties"
    )


class FooProfileProperties(ProfileProperties):
    foo: Property = Property("Foo")


@dataclass(frozen=True)
class BarProfileProperties:
    bar: Property = Property("Bar")


def test_init_profile_properties():
    """Test initialization of self.profile_properties."""
    user = _make_user()

    # default ProfileProperties
    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.testing": True})
    assert mixpanel.profile_properties == ProfileProperties()

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        user=user,
        settings={
            "mixpanel.testing": True,
            "mixpanel.profile_properties": "pyramid_mixpanel.tests.test_track.FooProfileProperties",
        },
    )
    assert mixpanel.profile_properties == FooProfileProperties()

    # the resolved ProfileProperties need to be based off of
    # pyramid_mixpanel.ProfileProperties to contain the profile properties
    # that this library expects
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            user=user,
            settings={
                "mixpanel.testing": True,
                "mixpanel.profile_properties": "pyramid_mixpanel.tests.test_track.BarProfileProperties",
            },
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on pyramid_mixpanel.ProfileProperties"
    )

    # passing ProfileProperties as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            user=user,
            settings={  # type: ignore
                "mixpanel.testing": True,
                "mixpanel.profile_properties": FooProfileProperties(),
            },
        )
    assert (
        str(exc.value)
        == "dotted_name must be a string, but it is: FooProfileProperties"
    )


class FooProfileMetaProperties(ProfileMetaProperties):
    foo: Property = Property("Foo")


@dataclass(frozen=True)
class BarProfileMetaProperties:
    bar: Property = Property("Bar")


def test_init_profile_meta_properties():
    """Test initialization of self.profile_meta_properties."""
    user = _make_user()

    # default ProfileMetaProperties
    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.testing": True})
    assert mixpanel.profile_meta_properties == ProfileMetaProperties()

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        user=user,
        settings={
            "mixpanel.testing": True,
            "mixpanel.profile_meta_properties": "pyramid_mixpanel.tests.test_track.FooProfileMetaProperties",
        },
    )
    assert mixpanel.profile_meta_properties == FooProfileMetaProperties()

    # the resolved ProfileMetaProperties need to be based off of
    # pyramid_mixpanel.ProfileMetaProperties to contain the profile properties
    # that this library expects
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            user=user,
            settings={
                "mixpanel.testing": True,
                "mixpanel.profile_meta_properties": "pyramid_mixpanel.tests.test_track.BarProfileMetaProperties",
            },
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on pyramid_mixpanel.ProfileMetaProperties"
    )

    # passing ProfileMetaProperties as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            user=user,
            settings={  # type: ignore
                "mixpanel.testing": True,
                "mixpanel.profile_meta_properties": FooProfileMetaProperties(),
            },
        )
    assert (
        str(exc.value)
        == "dotted_name must be a string, but it is: FooProfileMetaProperties"
    )


@freeze_time("2018-01-01")
def test_track():
    """Test the track method."""
    user = _make_user()
    m = MixpanelTrack(user=user, settings={"mixpanel.testing": True})

    m.track(Events.user_logged_in)
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "events"
    assert m.api._consumer.mocked_messages[0].msg == {
        "event": "User Logged In",
        "properties": {
            "token": "testing",
            "distinct_id": "distinct id",
            "time": 1514764800,  # 2018-01-01
            "mp_lib": "python",
            "$lib_version": "4.4.0",
        },
    }

    m.track(
        Events.page_viewed,
        {
            EventProperties.path: "/about",
            EventProperties.title: "About Us",
            EventProperties.dollar_referrer: "https://niteo.co",
        },
    )
    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[1].endpoint == "events"
    assert m.api._consumer.mocked_messages[1].msg == {
        "event": "Page Viewed",
        "properties": {
            "token": "testing",
            "distinct_id": "distinct id",
            "time": 1514764800,  # 2018-01-01
            "mp_lib": "python",
            "$lib_version": "4.4.0",
            "$referrer": "https://niteo.co",
            "Path": "/about",
            "Title": "About Us",
        },
    }


# @freeze_time("2018-01-01")
# def test_profile_sync(db, users):
#     """Test the profile_sync method."""
#     user = db.query(User).filter(User.id == USER_ONE_ID).one()

#     m = MixpanelTrack(user=user, settings={"mixpanel.token": "secret"})
#     m.api = mock.Mock(spec="people_set _consumer".split())

#     m.profile_sync()
#     m.api.people_set.assert_called_with(
#         "mixpanel-distinct-id-1",
#         {
#             "$email": "one@bar.com",
#             "$created": "2018-01-02T00:00:00",
#             "State": "no_subscription",
#         },
#         {},
#     )


#     m.profile_sync(extra={"foo": "bar"}, meta={"$foo": "ban"})
#     m.api.people_set.assert_called_with(
#         "mixpanel-distinct-id-1",
#         {
#             "$email": "one@bar.com",
#             "$created": "2018-01-02T00:00:00",
#             "State": "no_subscription",
#             "foo": "bar",
#         },
#         {"$foo": "ban"},
#     )


# @freeze_time("2018-01-01")
# def test_profile_set(db, users):
#     """Test the profile_sync method."""
#     user = db.query(User).filter(User.id == USER_ONE_ID).one()

#     m = MixpanelTrack(user=user, settings={"mixpanel.token": "secret"})
#     m.api = mock.Mock(spec="people_set _consumer".split())

#     m.profile_set(props={"foo": "bar"})
#     m.api.people_set.assert_called_with("mixpanel-distinct-id-1", {"foo": "bar"}, {})

#     m.profile_set(props={"foo": "bar"}, meta={"$foo": "ban"})
#     m.api.people_set.assert_called_with(
#         "mixpanel-distinct-id-1", {"foo": "bar"}, {"$foo": "ban"}
#     )


# @freeze_time("2018-01-01")
# def test_profile_increment(db, users):
#     """Test the profile_increment method."""
#     user = db.query(User).filter(User.id == USER_ONE_ID).one()

#     m = MixpanelTrack(user=user, settings={"mixpanel.token": "secret"})
#     m.api = mock.Mock(spec="people_increment _consumer".split())

#     m.profile_increment(props={"foo": 1})
#     m.api.people_increment.assert_called_with("mixpanel-distinct-id-1", {"foo": 1})


# @freeze_time("2018-01-01")
# def test_profile_track_charge(db, users):
#     """Test the profile_track_charge method."""
#     user = db.query(User).filter(User.id == USER_ONE_ID).one()

#     m = MixpanelTrack(user=user, settings={"mixpanel.token": "secret"})
#     m.api = mock.Mock(spec="people_track_charge _consumer".split())

#     m.profile_track_charge(100, props={"foo": "bar"})
#     m.api.people_track_charge.assert_called_with(
#         "mixpanel-distinct-id-1", 100, {"foo": "bar"}
#     )


# def test_bad_event_name():
#     """Test the track method fails on bad event name."""
#     user = mock.Mock()

#     class FooEvents(Enum):
#         foo = "Foo"

#     with pytest.raises(Exception) as exc:
#         MixpanelTrack(
#             user=user, settings={"mixpanel.testing": True, "mixpanel.events": FooEvents}
#         ).track(FooEvents.foo)

#     assert str(exc.value) == "Unknown mixpanel event: Foo"
