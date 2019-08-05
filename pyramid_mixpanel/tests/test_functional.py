"""Functional tests against a real Pyramid app."""

from freezegun import freeze_time
from mixpanel import json_dumps
from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.router import Router
from pyramid.view import view_config
from pyramid_mixpanel import EventProperties
from pyramid_mixpanel import Events
from pyramid_mixpanel.consumer import MockedMessage
from pyramid_mixpanel.tests.test_track import _make_user
from testfixtures import LogCapture
from unittest import mock
from webtest import TestApp

import base64
import structlog
import typing as t
import urllib


@view_config(route_name="hello", renderer="json", request_method="GET")
def hello(request: Request) -> t.Dict[str, str]:
    """Say hello."""
    # mocking that request has a user object
    request.user = _make_user()

    # provide access to Pyramid request in WebTest response
    request.environ["paste.testing_variables"]["app_request"] = request

    request.mixpanel.track(Events.page_viewed, {EventProperties.path: "/hello"})
    return {"hello": "world"}


def app(settings) -> Router:
    """Create a dummy Pyramid app."""
    structlog.configure(
        processors=[structlog.processors.KeyValueRenderer(sort_keys=True)],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    with Configurator() as config:
        config.add_route("hello", "/hello")
        config.scan(".")

        config.registry.settings.update(**settings)
        config.include("pyramid_mixpanel")

        return config.make_wsgi_app()


@freeze_time("2019-01-01")
def test_MockedConsumer() -> None:
    """Test that request.mixpanel works as expected with MockedConsumer."""
    with LogCapture() as logs:
        settings = {"mixpanel.testing": "true"}
        testapp = TestApp(app(settings))

        res = testapp.get("/hello", status=200)
        assert res.json == {"hello": "world"}

    logs.check(
        (
            "pyramid_mixpanel.track",
            "INFO",
            "consumer='MockedConsumer' event='request.mixpanel configured' "
            "event_properties='EventProperties' events='Events' "
            "profile_meta_properties='ProfileMetaProperties' "
            "profile_properties='ProfileProperties'",
        ),
        (
            "pyramid_mixpanel.track",
            "WARNING",
            "event='mixpanel is in testing mode, no message will be sent'",
        ),
    )

    res.app_request.mixpanel.api._consumer.mocked_messages == [
        MockedMessage(
            endpoint="events",
            msg={
                "event": "Page Viewed",
                "properties": {
                    "token": "testing",
                    "distinct_id": "distinct id",
                    "time": 1564322909,
                    "mp_lib": "python",
                    "$lib_version": "4.4.0",
                    "Path": "/hello",
                },
            },
        )
    ]


@freeze_time("2019-01-01")
@mock.patch("mixpanel.urllib.request.urlopen")
@mock.patch("mixpanel.urllib.request.Request")
def test_PoliteBufferedConsumer(
    request: mock.MagicMock, urlopen: mock.MagicMock
) -> None:
    """Test that request.mixpanel works as expected with PoliteBufferedConsumer."""
    urlopen().read.return_value = b'{"error":null,"status":1}'

    with LogCapture() as logs:
        settings = {"mixpanel.token": "SECRET"}
        testapp = TestApp(app(settings))

        res = testapp.get("/hello", status=200)
        assert res.json == {"hello": "world"}

    logs.check(
        (
            "pyramid_mixpanel.track",
            "INFO",
            "consumer='PoliteBufferedConsumer' event='request.mixpanel configured' "
            "event_properties='EventProperties' events='Events' "
            "profile_meta_properties='ProfileMetaProperties' "
            "profile_properties='ProfileProperties'",
        )
    )

    message = json_dumps(
        [
            {
                "event": "Page Viewed",
                "properties": {
                    "token": "SECRET",
                    "distinct_id": "distinct id",
                    "time": 1546300800,
                    "mp_lib": "python",
                    "$lib_version": "4.4.0",
                    "Path": "/hello",
                },
            }
        ]
    )
    data = {"data": base64.b64encode(message.encode("utf8")), "verbose": 1, "ip": 0}
    request.assert_called_with(
        "https://api.mixpanel.com/track",
        urllib.parse.urlencode(data).encode("utf8"),  # type:ignore
    )