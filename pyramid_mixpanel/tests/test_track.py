"""Tests for Mixpanel tracking."""

from pyramid_mixpanel import MixpanelTrack
from pyramid_mixpanel import MockedConsumer
from pyramid_mixpanel import QueuedConsumer
from unittest import mock

# import mixpanel
# import pytest


def test_init():
    """Test initialization of MixpanelTrack class."""
    user = mock.Mock(spec=" ".split())

    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.token": "secret"})
    assert mixpanel.user == user
    assert mixpanel.api._consumer.__class__ == QueuedConsumer

    mixpanel = MixpanelTrack(user=user, settings={"mixpanel.testing": "true"})
    assert mixpanel.user == user
    assert mixpanel.api._consumer.__class__ == MockedConsumer


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


# @freeze_time("2018-01-01")
# def test_track(db, users):
#     """Test the track method."""
#     user = db.query(User).filter(User.id == USER_ONE_ID).one()

#     m = MixpanelTrack(user=user, settings={"mixpanel.token": "secret"})
#     m.api = mock.Mock(spec="track _consumer".split())

#     m.track("User Logged In")
#     m.api.track.assert_called_with("mixpanel-distinct-id-1", "User Logged In", {})

#     m.track("User Logged In", {"foo": "bar"})
#     m.api.track.assert_called_with(
#         "mixpanel-distinct-id-1", "User Logged In", {"foo": "bar"}
#     )


# def test_bad_event_name():
#     """Test the track method fails on bad event name."""
#     user = mock.Mock()

#     with pytest.raises(Exception) as exc:
#         MixpanelTrack(user=user, settings={"mixpanel.token": "secret"}).track("Foo")

#     assert str(exc.value) == "Unknown mixpanel event: Foo"
