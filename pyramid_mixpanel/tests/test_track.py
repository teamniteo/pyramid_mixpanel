"""Tests for Mixpanel tracking."""

from dataclasses import dataclass
from freezegun import freeze_time
from pyramid_mixpanel import Event
from pyramid_mixpanel import EventProperties
from pyramid_mixpanel import Events
from pyramid_mixpanel import ProfileMetaProperties
from pyramid_mixpanel import ProfileProperties
from pyramid_mixpanel import Property
from pyramid_mixpanel.consumer import MockedConsumer
from pyramid_mixpanel.consumer import PoliteBufferedConsumer
from pyramid_mixpanel.track import MixpanelTrack
from unittest import mock

import pytest


def test_mixpanel_init_distinct_id() -> None:
    """Test distinct_id is set in mixpanel_init function."""
    from pyramid_mixpanel.track import mixpanel_init

    # Requests without request.user
    request = mock.Mock(spec="registry".split())
    request.registry.settings = {}

    result = mixpanel_init(request)

    assert result.__class__ == MixpanelTrack
    assert result.distinct_id is None

    # Requests with request.user
    request = mock.Mock(spec="registry user".split())
    request.registry.settings = {}
    request.user.distinct_id = "foo"

    result = mixpanel_init(request)

    assert result.__class__ == MixpanelTrack
    assert result.distinct_id == "foo"


def test_init_consumers() -> None:
    """Test initialization of Consumer."""
    mixpanel = MixpanelTrack(settings={"mixpanel.token": "secret"})
    assert mixpanel.api._consumer.__class__ == PoliteBufferedConsumer

    mixpanel = MixpanelTrack(settings={})
    assert mixpanel.api._consumer.__class__ == MockedConsumer


@dataclass(frozen=True)
class FooEvents(Events):
    foo: Event = Event("Foo")


@dataclass(frozen=True)
class BarEvents:
    bar: Event = Event("Bar")


def test_init_events() -> None:
    """Test initialization of self.events."""
    # default Events
    mixpanel = MixpanelTrack(settings={})
    assert mixpanel.events == Events()

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        settings={"mixpanel.events": "pyramid_mixpanel.tests.test_track.FooEvents"}
    )
    assert mixpanel.events == FooEvents()

    # the resolved Events need to be based off of pyramid_mixpanel.Events
    # to contain the events that this library expects
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={"mixpanel.events": "pyramid_mixpanel.tests.test_track.BarEvents"}
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on pyramid_mixpanel.Events"
    )

    # passing Events as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={"mixpanel.events": FooEvents()}  # type: ignore
        )
    assert str(exc.value) == "dotted_name must be a string, but it is: FooEvents"


class FooEventProperties(EventProperties):
    foo: Property = Property("Foo")


@dataclass(frozen=True)
class BarEventProperties:
    bar: Property = Property("Bar")


def test_init_event_properties() -> None:
    """Test initialization of self.event_properties."""
    # default EventProperties
    mixpanel = MixpanelTrack(settings={})
    assert mixpanel.event_properties == EventProperties()

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        settings={
            "mixpanel.event_properties": "pyramid_mixpanel.tests.test_track.FooEventProperties"
        }
    )
    assert mixpanel.event_properties == FooEventProperties()

    # the resolved EventProperties need to be based off of
    # pyramid_mixpanel.EventProperties to contain the event properties
    # that this library expects
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={
                "mixpanel.event_properties": "pyramid_mixpanel.tests.test_track.BarEventProperties"
            }
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on pyramid_mixpanel.EventProperties"
    )

    # passing EventProperties as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={"mixpanel.event_properties": FooEventProperties()}  # type: ignore
        )
    assert (
        str(exc.value) == "dotted_name must be a string, but it is: FooEventProperties"
    )


class FooProfileProperties(ProfileProperties):
    foo: Property = Property("Foo")


@dataclass(frozen=True)
class BarProfileProperties:
    bar: Property = Property("Bar")


def test_init_profile_properties() -> None:
    """Test initialization of self.profile_properties."""
    # default ProfileProperties
    mixpanel = MixpanelTrack(settings={})
    assert mixpanel.profile_properties == ProfileProperties()

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        settings={
            "mixpanel.profile_properties": "pyramid_mixpanel.tests.test_track.FooProfileProperties"
        }
    )
    assert mixpanel.profile_properties == FooProfileProperties()

    # the resolved ProfileProperties need to be based off of
    # pyramid_mixpanel.ProfileProperties to contain the profile properties
    # that this library expects
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={
                "mixpanel.profile_properties": "pyramid_mixpanel.tests.test_track.BarProfileProperties"
            }
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on pyramid_mixpanel.ProfileProperties"
    )

    # passing ProfileProperties as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={  # type: ignore
                "mixpanel.profile_properties": FooProfileProperties()
            }
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


def test_init_profile_meta_properties() -> None:
    """Test initialization of self.profile_meta_properties."""
    # default ProfileMetaProperties
    mixpanel = MixpanelTrack(settings={})
    assert mixpanel.profile_meta_properties == ProfileMetaProperties()

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        settings={
            "mixpanel.profile_meta_properties": "pyramid_mixpanel.tests.test_track.FooProfileMetaProperties"
        }
    )
    assert mixpanel.profile_meta_properties == FooProfileMetaProperties()

    # the resolved ProfileMetaProperties need to be based off of
    # pyramid_mixpanel.ProfileMetaProperties to contain the profile properties
    # that this library expects
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={
                "mixpanel.profile_meta_properties": "pyramid_mixpanel.tests.test_track.BarProfileMetaProperties"
            }
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on pyramid_mixpanel.ProfileMetaProperties"
    )

    # passing ProfileMetaProperties as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={  # type: ignore
                "mixpanel.profile_meta_properties": FooProfileMetaProperties()
            }
        )
    assert (
        str(exc.value)
        == "dotted_name must be a string, but it is: FooProfileMetaProperties"
    )


@freeze_time("2018-01-01")
def test_track() -> None:
    """Test the track method."""
    m = MixpanelTrack(settings={}, distinct_id="foo")

    m.track(Events.user_logged_in)
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "events"
    assert m.api._consumer.mocked_messages[0].msg == {
        "event": "User Logged In",
        "properties": {
            "token": "testing",
            "distinct_id": "foo",
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
            "distinct_id": "foo",
            "time": 1514764800,  # 2018-01-01
            "mp_lib": "python",
            "$lib_version": "4.4.0",
            "$referrer": "https://niteo.co",
            "Path": "/about",
            "Title": "About Us",
        },
    }

    # should fail if distinct_id is None
    m = MixpanelTrack(settings={})
    with pytest.raises(AttributeError) as exc:
        m.track(Events.user_logged_in)
    assert (
        str(exc.value)
        == "distinct_id must be set before you can send events or set properties"
    )


@freeze_time("2018-01-01")
def test_profile_set() -> None:
    """Test the profile_set method."""
    m = MixpanelTrack(settings={}, distinct_id="foo")

    m.profile_set({ProfileProperties.dollar_name: "FooBar"})
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800000,
        "$distinct_id": "foo",
        "$set": {"$name": "FooBar"},
    }

    # with meta properties
    m.profile_set(
        {ProfileProperties.dollar_name: "FooBar2"},
        meta={ProfileMetaProperties.dollar_ip: "1.1.1.1"},
    )
    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[1].endpoint == "people"
    assert m.api._consumer.mocked_messages[1].msg == {
        "$token": "testing",
        "$time": 1514764800000,
        "$distinct_id": "foo",
        "$set": {"$name": "FooBar2"},
        "$ip": "1.1.1.1",
    }


@freeze_time("2018-01-01")
def test_people_append() -> None:
    """Test the people_append method."""
    m = MixpanelTrack(settings={}, distinct_id="foo")

    m.people_append({ProfileProperties.dollar_name: "FooBar"})
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800000,
        "$distinct_id": "foo",
        "$append": {"$name": "FooBar"},
    }

    # with meta properties
    m.people_append(
        {ProfileProperties.dollar_name: "FooBar2"},
        meta={ProfileMetaProperties.dollar_ip: "1.1.1.1"},
    )
    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[1].endpoint == "people"
    assert m.api._consumer.mocked_messages[1].msg == {
        "$token": "testing",
        "$time": 1514764800000,
        "$distinct_id": "foo",
        "$append": {"$name": "FooBar2"},
        "$ip": "1.1.1.1",
    }


@freeze_time("2018-01-01")
def test_profile_increment() -> None:
    """Test the profile_increment method."""
    m = MixpanelTrack(
        settings={
            "mixpanel.profile_events": "pyramid_mixpanel.tests.test_track.FooProfileProperties"
        },
        distinct_id="foo",
    )

    m.profile_increment(props={FooProfileProperties.foo: 1})
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800000,
        "$distinct_id": "foo",
        "$add": {"Foo": 1},
    }


@freeze_time("2018-01-01")
def test_profile_track_charge() -> None:
    """Test the profile_track_charge method."""
    m = MixpanelTrack(
        settings={
            "mixpanel.profile_events": "pyramid_mixpanel.tests.test_track.FooProfileProperties"
        },
        distinct_id="foo",
    )

    m.profile_track_charge(100)
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800000,
        "$distinct_id": "foo",
        "$append": {"$transactions": {"$amount": 100}},
    }

    m.profile_track_charge(222, props={FooProfileProperties.foo: "Bar"})
    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[1].endpoint == "people"
    assert m.api._consumer.mocked_messages[1].msg == {
        "$token": "testing",
        "$time": 1514764800000,
        "$distinct_id": "foo",
        "$append": {"$transactions": {"Foo": "Bar", "$amount": 222}},
    }
