"""Tests for Mixpanel tracking."""

# from enum import Enum
from freezegun import freeze_time
from pyramid_mixpanel import Events
from pyramid_mixpanel import MixpanelTrack
from pyramid_mixpanel import MockedConsumer
from pyramid_mixpanel import QueuedConsumer
from unittest import mock

# import mixpanel
# import pytest


def _make_user(distinct_id="distinct id"):
    user = mock.Mock(spec="distinct_id".split())
    user.distinct_id = distinct_id
    return user


def test_init():
    """Test initialization of MixpanelTrack class."""
    user = _make_user()

    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.token": "secret"})
    assert mixpanel.user == user
    assert mixpanel.api._consumer.__class__ == QueuedConsumer

    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.testing": "true"})
    assert mixpanel.user == user
    assert mixpanel.api._consumer.__class__ == MockedConsumer


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

    m.track(Events.user_logged_in, {"foo": "bar"})
    assert len(m.api._consumer.mocked_messages) == 2
    assert m.api._consumer.mocked_messages[1].endpoint == "events"
    assert m.api._consumer.mocked_messages[1].msg == {
        "event": "User Logged In",
        "properties": {
            "token": "testing",
            "distinct_id": "distinct id",
            "time": 1514764800,  # 2018-01-01
            "mp_lib": "python",
            "$lib_version": "4.4.0",
            "foo": "bar",
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
