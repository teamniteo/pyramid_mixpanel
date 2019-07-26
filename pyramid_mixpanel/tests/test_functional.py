"""Functional tests against a real Pyramid app."""

from freezegun import freeze_time
from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.router import Router
from pyramid.view import view_config
from pyramid_mixpanel import EventProperties
from pyramid_mixpanel import Events
from pyramid_mixpanel.tests.test_track import _make_user
from unittest import mock
from webtest import TestApp

import typing as t


@view_config(route_name="hello", renderer="json", request_method="GET")
def hello(request: Request) -> t.Dict[str, str]:
    """Say hello."""
    request.user = _make_user()  # mocking that request has a user object

    request.mixpanel.track(Events.page_viewed, {EventProperties.path: "/hello"})
    return {"hello": "world"}


def app() -> Router:
    """Create a dummy Pyramid app."""
    with Configurator() as config:
        config.add_route("hello", "/hello")
        config.scan(".")

        config.registry.settings["mixpanel.testing"] = True
        config.include("pyramid_mixpanel")

        return config.make_wsgi_app()


@mock.patch("pyramid_mixpanel.MockedConsumer")
@freeze_time("2018-01-01")
def test_mixpanel_request_accessor(mocked_consumer) -> None:
    """Test that request.mixpanel works as expected."""
    testapp = TestApp(app())

    res = testapp.get("/hello", status=200)
    assert res.json == {"hello": "world"}

    mocked_consumer().send.assert_called_with(
        "events",
        '{"event":"Page Viewed","properties":{"token":"testing",'
        '"distinct_id":"distinct id","time":1514764800,"mp_lib":"python",'
        '"$lib_version":"4.4.0","Path":"/hello"}}',
    )
