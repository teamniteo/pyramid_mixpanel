"""Tests for Mixpanel tracking."""

from customerio.track import CustomerIO
from dataclasses import dataclass
from freezegun import freeze_time
from mixpanel import Consumer
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
    request = mock.Mock(spec="registry headers".split())
    request.registry.settings = {}
    request.headers = {}

    result = mixpanel_init(request)

    assert result.__class__ == MixpanelTrack
    assert result.distinct_id is None

    # Requests with request.user
    request = mock.Mock(spec="registry headers user".split())
    request.registry.settings = {}
    request.headers = {}
    request.user.distinct_id = "foo"

    result = mixpanel_init(request)

    assert result.__class__ == MixpanelTrack
    assert result.distinct_id == "foo"


class FooConsumer(Consumer):
    pass


class BarConsumer(object):
    pass


def test_init_consumers() -> None:
    """Test initialization of Consumer."""

    # default consumer
    mixpanel = MixpanelTrack(settings={"mixpanel.token": "secret"})
    assert isinstance(mixpanel.api._consumer, PoliteBufferedConsumer)  # noqa: SF01

    # if token is not set, use MockedConsumer
    mixpanel = MixpanelTrack(settings={})
    assert mixpanel.api._consumer == MockedConsumer()  # noqa: SF01

    # resolved from a dotted-name
    mixpanel = MixpanelTrack(
        settings={
            "mixpanel.token": "secret",
            "mixpanel.consumer": "pyramid_mixpanel.tests.test_track.FooConsumer",
        }
    )
    assert isinstance(mixpanel.api._consumer, FooConsumer)  # noqa: SF01

    # the resolved Consumer needs to be based off of
    # mixpanel.(Buffered)Consumer to have the expected API
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={
                "mixpanel.consumer": "pyramid_mixpanel.tests.test_track.BarConsumer"
            }
        )
    assert (
        str(exc.value)
        == "class in dotted_name needs to be based on mixpanel.(Buffered)Consumer"
    )

    # passing Consumer as an object is not (yet) supported
    with pytest.raises(ValueError) as exc:
        mixpanel = MixpanelTrack(
            settings={"mixpanel.consumer": FooConsumer()}  # type: ignore
        )
    assert str(exc.value) == "dotted_name must be a string, but it is: FooConsumer"


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


@dataclass(frozen=True)
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


def test_mixpanel_init_customerio() -> None:
    """Test customerio api object is created."""
    from pyramid_mixpanel.track import mixpanel_init

    # By default, Customer.io is not configured
    request = mock.Mock(spec="registry headers".split())
    request.registry.settings = {}
    request.headers = {}

    result = mixpanel_init(request)

    assert result.__class__ == MixpanelTrack
    assert result.cio is None

    # However if correct settings are provided, Customer.io API object is created
    request.registry.settings = {
        "customerio.tracking.site_id": "secret",
        "customerio.tracking.api_key": "secret",
        "customerio.tracking.region": "eu",
    }

    result = mixpanel_init(request)
    assert result.__class__ == MixpanelTrack
    assert result.cio.__class__ == CustomerIO
    assert "eu" in result.cio.base_url

    # US region is also possible
    request.registry.settings["customerio.tracking.region"] = "us"

    result = mixpanel_init(request)
    assert "us" in result.cio.base_url

    # fail on bad region
    request.registry.settings["customerio.tracking.region"] = "foo"

    with pytest.raises(ValueError) as cm:
        result = mixpanel_init(request)
    assert str(cm.value) == "Unknown customer.io region"


@dataclass(frozen=True)
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
            settings={
                "mixpanel.profile_properties": FooProfileProperties()  # type: ignore
            }
        )
    assert (
        str(exc.value)
        == "dotted_name must be a string, but it is: FooProfileProperties"
    )


@dataclass(frozen=True)
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
            settings={
                "mixpanel.profile_meta_properties": FooProfileMetaProperties()  # type: ignore
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
    m.api._make_insert_id = lambda: "123e4567"  # noqa: SF01

    # default event
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
            "$lib_version": "4.9.0",
            "$insert_id": "123e4567",
        },
    }
    m.api._consumer.mocked_messages.clear()

    # default event with default properties
    m.track(
        Events.page_viewed,
        {
            EventProperties.path: "/about",
            EventProperties.title: "About Us",
            EventProperties.dollar_referrer: "https://niteo.co",
        },
    )
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "events"
    assert m.api._consumer.mocked_messages[0].msg == {
        "event": "Page Viewed",
        "properties": {
            "token": "testing",
            "distinct_id": "foo",
            "time": 1514764800,  # 2018-01-01
            "mp_lib": "python",
            "$lib_version": "4.9.0",
            "$insert_id": "123e4567",
            "$referrer": "https://niteo.co",
            "Path": "/about",
            "Title": "About Us",
        },
    }
    m.api._consumer.mocked_messages.clear()

    # custom event with custom properties
    m = MixpanelTrack(
        settings={
            "mixpanel.events": "pyramid_mixpanel.tests.test_track.FooEvents",
            "mixpanel.event_properties": "pyramid_mixpanel.tests.test_track.FooEventProperties",
        },
        distinct_id="foo",
    )
    m.api._make_insert_id = lambda: "123e4567"  # noqa: SF01
    m.track(FooEvents.foo, {FooEventProperties.foo: "bar"})
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "events"
    assert m.api._consumer.mocked_messages[0].msg == {
        "event": "Foo",
        "properties": {
            "token": "testing",
            "distinct_id": "foo",
            "time": 1514764800,
            "mp_lib": "python",
            "$lib_version": "4.9.0",
            "$insert_id": "123e4567",
            "Foo": "bar",
        },
    }

    m.api._consumer.mocked_messages.clear()

    # global event property is added to all events
    m = MixpanelTrack(
        settings={
            "mixpanel.events": "pyramid_mixpanel.tests.test_track.FooEvents",
            "mixpanel.event_properties": "pyramid_mixpanel.tests.test_track.FooEventProperties",
        },
        distinct_id="foo",
        global_event_props={FooEventProperties.foo: "bar"},
    )
    m.api._make_insert_id = lambda: "123e4567"  # noqa: SF01
    m.track(FooEvents.foo, {})
    m.track(FooEvents.foo, {})
    # override global event property
    m.track(FooEvents.foo, {FooEventProperties.foo: "baz"})
    assert len(m.api._consumer.mocked_messages) == 3
    assert m.api._consumer.mocked_messages[0].endpoint == "events"
    assert m.api._consumer.mocked_messages[0].msg == {
        "event": "Foo",
        "properties": {
            "token": "testing",
            "distinct_id": "foo",
            "time": 1514764800,
            "mp_lib": "python",
            "$lib_version": "4.9.0",
            "$insert_id": "123e4567",
            "Foo": "bar",
        },
    }
    assert m.api._consumer.mocked_messages[1].endpoint == "events"
    assert m.api._consumer.mocked_messages[1].msg == {
        "event": "Foo",
        "properties": {
            "token": "testing",
            "distinct_id": "foo",
            "time": 1514764800,
            "mp_lib": "python",
            "$lib_version": "4.9.0",
            "$insert_id": "123e4567",
            "Foo": "bar",
        },
    }
    assert m.api._consumer.mocked_messages[2].endpoint == "events"
    assert m.api._consumer.mocked_messages[2].msg == {
        "event": "Foo",
        "properties": {
            "token": "testing",
            "distinct_id": "foo",
            "time": 1514764800,
            "mp_lib": "python",
            "$lib_version": "4.9.0",
            "$insert_id": "123e4567",
            "Foo": "baz",
        },
    }

    m.api._consumer.mocked_messages.clear()


@freeze_time("2018-01-01")
def test_track_customerio() -> None:
    """Test tracking an event at Customer.io."""

    m = MixpanelTrack(
        settings={
            "customerio.tracking.site_id": "foo",
            "customerio.tracking.api_key": "secret",
            "customerio.tracking.region": "eu",
        },
        distinct_id="foo",
    )
    m.api._make_insert_id = lambda: "123e4567"  # noqa: SF01

    m.track(
        Events.page_viewed,
        {
            EventProperties.path: "/about",
            EventProperties.title: "About Us",
            EventProperties.dollar_referrer: "https://niteo.co",
        },
    )
    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[0].endpoint == "events"
    assert m.api._consumer.mocked_messages[0].msg == {
        "event": "Page Viewed",
        "properties": {
            "token": "testing",
            "distinct_id": "foo",
            "time": 1514764800,  # 2018-01-01
            "mp_lib": "python",
            "$lib_version": "4.9.0",
            "$insert_id": "123e4567",
            "$referrer": "https://niteo.co",
            "Path": "/about",
            "Title": "About Us",
        },
    }

    assert m.api._consumer.mocked_messages[1].endpoint == "customer.io"
    assert m.api._consumer.mocked_messages[1].msg == {
        "Path": "/about",
        "Title": "About Us",
        "customer_id": "foo",  # this is distinct_id
        "name": "Page Viewed",
        "referrer": "https://niteo.co",  # dollar sign was removed
    }
    m.api._consumer.mocked_messages.clear()


def test_track_guards() -> None:
    """Test guards that make sure parameters sent to .track() are good."""

    # fail if distinct_id is None
    m = MixpanelTrack(settings={})
    with pytest.raises(AttributeError) as exc:
        m.track(Events.user_logged_in)
    assert (
        str(exc.value)
        == "distinct_id must be set before you can send events or set properties"
    )

    # fail if event is not a member of mixpanel.events
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.track(FooEvents.foo)
    assert str(exc.value) == "Event 'Event(name='Foo')' is not a member of self.events"

    # fail if event property is not a member of mixpanel.event_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.track(Events.user_logged_in, {FooEventProperties.foo: "foo"})
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.event_properties"
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
        "$time": 1514764800,
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
        "$time": 1514764800,
        "$distinct_id": "foo",
        "$set": {"$name": "FooBar2"},
        "$ip": "1.1.1.1",
    }


@freeze_time("2018-01-01")
def test_profile_set_customerio() -> None:
    """Test setting a profile property on Customer.io."""
    m = MixpanelTrack(
        settings={
            "customerio.tracking.site_id": "foo",
            "customerio.tracking.api_key": "secret",
            "customerio.tracking.region": "eu",
        },
        distinct_id="foo",
    )
    m.profile_set(
        {ProfileProperties.dollar_name: "FooBar"},
        meta={ProfileMetaProperties.dollar_ip: "1.1.1.1"},
    )

    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800,
        "$distinct_id": "foo",
        "$set": {"$name": "FooBar"},
        "$ip": "1.1.1.1",
    }

    assert m.api._consumer.mocked_messages[1].endpoint == "customer.io"
    assert m.api._consumer.mocked_messages[1].msg == {
        "id": "foo",  # this is distinct_id
        "name": "FooBar",
        "ip": "1.1.1.1",  # dollar sign was removed
    }


def test_profile_set_guards() -> None:
    """Test guards that make sure parameters sent to .profile_set() are good."""

    # fail if distinct_id is None
    m = MixpanelTrack(settings={})
    with pytest.raises(AttributeError) as exc:
        m.profile_set({ProfileProperties.dollar_name: "FooBar"})
    assert (
        str(exc.value)
        == "distinct_id must be set before you can send events or set properties"
    )

    # fail if property is not a member of mixpanel.profile_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.profile_set({FooProfileProperties.foo: "bar"})
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.profile_properties"
    )

    # fail if meta property is not a member of mixpanel.profile_meta_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.profile_set(
            {ProfileProperties.dollar_name: "foo"},
            meta={FooProfileMetaProperties.foo: "bar"},
        )
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.profile_meta_properties"
    )


@freeze_time("2018-01-01")
def test_people_append() -> None:
    """Test the people_append method."""
    m = MixpanelTrack(settings={}, distinct_id="foo")

    m.people_append({ProfileProperties.dollar_name: "FooBar"})
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800,
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
        "$time": 1514764800,
        "$distinct_id": "foo",
        "$append": {"$name": "FooBar2"},
        "$ip": "1.1.1.1",
    }


def test_people_append_guards() -> None:
    """Test guards that make sure parameters sent to .people_append() are good."""

    # fail if distinct_id is None
    m = MixpanelTrack(settings={})
    with pytest.raises(AttributeError) as exc:
        m.people_append({ProfileProperties.dollar_name: "FooBar"})
    assert (
        str(exc.value)
        == "distinct_id must be set before you can send events or set properties"
    )

    # fail if property is not a member of mixpanel.profile_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.people_append({FooProfileProperties.foo: "FooBar"})
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.profile_properties"
    )

    # fail if meta property is not a member of mixpanel.profile_meta_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.people_append(
            {ProfileProperties.dollar_name: "foo"},
            meta={FooProfileMetaProperties.foo: "bar"},
        )
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.profile_meta_properties"
    )


@freeze_time("2018-01-01")
def test_people_union() -> None:
    """Test the people_union method."""
    m = MixpanelTrack(settings={}, distinct_id="foo")

    m.people_union({ProfileProperties.dollar_name: ["FooBar"]})
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800,
        "$distinct_id": "foo",
        "$union": {"$name": ["FooBar"]},
    }

    # with meta properties
    m.people_union(
        {ProfileProperties.dollar_name: ["FooBar2"]},
        meta={ProfileMetaProperties.dollar_ip: ["1.1.1.1"]},
    )
    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[1].endpoint == "people"
    assert m.api._consumer.mocked_messages[1].msg == {
        "$token": "testing",
        "$time": 1514764800,
        "$distinct_id": "foo",
        "$union": {"$name": ["FooBar2"]},
        "$ip": ["1.1.1.1"],
    }


def test_people_union_guards() -> None:
    """Test guards that make sure parameters sent to .people_union() are good."""

    # fail if distinct_id is None
    m = MixpanelTrack(settings={})
    with pytest.raises(AttributeError) as exc:
        m.people_union({ProfileProperties.dollar_name: ["FooBar"]})
    assert (
        str(exc.value)
        == "distinct_id must be set before you can send events or set properties"
    )

    # fail if property is not a member of mixpanel.profile_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.people_union({FooProfileProperties.foo: ["FooBar"]})
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.profile_properties"
    )

    # fail if property's value is not a list
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(TypeError) as exc:  # type: ignore
        m.people_union({ProfileProperties.dollar_name: "FooBar"})
    assert str(exc.value) == "Property 'Property(name='$name')' value is not a list"

    # fail if meta property is not a member of mixpanel.profile_meta_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.people_union(
            {ProfileProperties.dollar_name: ["foo"]},
            meta={FooProfileMetaProperties.foo: ["bar"]},
        )
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.profile_meta_properties"
    )

    # fail if meta property's value is not a list
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(TypeError) as exc:  # type: ignore
        m.people_union(
            {ProfileProperties.dollar_name: ["foo"]},
            meta={ProfileMetaProperties.dollar_ip: "1.1.1.1"},
        )
    assert str(exc.value) == "Property 'Property(name='$ip')' value is not a list"


@freeze_time("2018-01-01")
def test_profile_increment() -> None:
    """Test the profile_increment method."""
    m = MixpanelTrack(
        settings={
            "mixpanel.profile_properties": "pyramid_mixpanel.tests.test_track.FooProfileProperties"
        },
        distinct_id="foo",
    )

    m.profile_increment(props={FooProfileProperties.foo: 1})
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800,
        "$distinct_id": "foo",
        "$add": {"Foo": 1},
    }


def test_profile_increment_guards() -> None:
    """Test guards that make sure parameters sent to .profile_increment() are good."""

    # fail if distinct_id is None
    m = MixpanelTrack(settings={})
    with pytest.raises(AttributeError) as exc:
        m.profile_increment({ProfileProperties.dollar_name: "FooBar"})
    assert (
        str(exc.value)
        == "distinct_id must be set before you can send events or set properties"
    )

    # fail if property is not a member of mixpanel.profile_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.profile_increment({FooProfileProperties.foo: "FooBar"})
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.profile_properties"
    )


@freeze_time("2018-01-01")
def test_profile_track_charge() -> None:
    """Test the profile_track_charge method."""
    m = MixpanelTrack(
        settings={
            "mixpanel.profile_properties": "pyramid_mixpanel.tests.test_track.FooProfileProperties"
        },
        distinct_id="foo",
    )

    m.profile_track_charge(100)
    assert len(m.api._consumer.mocked_messages) == 1
    assert m.api._consumer.mocked_messages[0].endpoint == "people"
    assert m.api._consumer.mocked_messages[0].msg == {
        "$token": "testing",
        "$time": 1514764800,
        "$distinct_id": "foo",
        "$append": {"$transactions": {"$amount": 100}},
    }

    m.profile_track_charge(222, props={FooProfileProperties.foo: "Bar"})
    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[1].endpoint == "people"
    assert m.api._consumer.mocked_messages[1].msg == {
        "$token": "testing",
        "$time": 1514764800,
        "$distinct_id": "foo",
        "$append": {"$transactions": {"Foo": "Bar", "$amount": 222}},
    }


def test_profile_track_charge_guards() -> None:
    """Test guards that make sure parameters sent to .profile_track_charge() are good."""

    # fail if distinct_id is None
    m = MixpanelTrack(settings={})
    with pytest.raises(AttributeError) as exc:
        m.profile_track_charge(100, {ProfileProperties.dollar_name: "FooBar"})
    assert (
        str(exc.value)
        == "distinct_id must be set before you can send events or set properties"
    )

    # fail if property is not a member of mixpanel.profile_properties
    m = MixpanelTrack(settings={}, distinct_id="foo")
    with pytest.raises(ValueError) as exc:  # type: ignore
        m.profile_track_charge(100, {FooProfileProperties.foo: "FooBar"})
    assert (
        str(exc.value)
        == "Property 'Property(name='Foo')' is not a member of self.profile_properties"
    )
