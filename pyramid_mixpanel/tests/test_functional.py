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
    request.user = mock.MagicMock(spec="distinct_id".split())
    request.user.distinct_id = "foo-123"

    # provide access to Pyramid request in WebTest response
    request.environ["paste.testing_variables"]["app_request"] = request

    request.mixpanel.track(Events.page_viewed, {EventProperties.path: "/hello"})
    return {"hello": "world"}


@view_config(route_name="bye", renderer="json", request_method="GET")
def bye(request: Request) -> t.Dict[str, str]:
    """Say bye."""
    return {"bye": "bye"}


def app(settings) -> Router:
    """Create a dummy Pyramid app."""
    structlog.configure(
        processors=[structlog.processors.KeyValueRenderer(sort_keys=True)],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    with Configurator() as config:
        config.add_route("hello", "/hello")
        config.add_route("bye", "/bye")
        config.scan(".")

        config.registry.settings.update(**settings)
        config.include("pyramid_mixpanel")

        return config.make_wsgi_app()


@freeze_time("2019-01-01")
def test_MockedConsumer() -> None:
    """Test that request.mixpanel works as expected with MockedConsumer."""
    with LogCapture() as logs:
        testapp = TestApp(app({"pyramid_heroku.structlog": True}))

        # do two requests to make sure logs are not flooded with messages
        # on every request
        res = testapp.get("/hello", status=200)
        res = testapp.get("/hello", status=200)
        assert res.json == {"hello": "world"}

    logs.check(
        (
            "pyramid_mixpanel",
            "INFO",
            "consumer='MockedConsumer' event='Mixpanel configured' "
            "event_properties='EventProperties' events='Events' "
            "profile_meta_properties='ProfileMetaProperties' "
            "profile_properties='ProfileProperties'",
        ),
        (
            "pyramid_mixpanel",
            "WARNING",
            "event='Mixpanel is in testing mode, no message will be sent!'",
        ),
    )

    assert res.app_request.mixpanel.api._consumer.flushed is True
    assert res.app_request.mixpanel.api._consumer.mocked_messages == [
        MockedMessage(
            endpoint="events",
            msg={
                "event": "Page Viewed",
                "properties": {
                    "token": "testing",
                    "distinct_id": "foo-123",
                    "time": 1546300800,
                    "mp_lib": "python",
                    "$lib_version": "4.5.0",
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
        settings = {"mixpanel.token": "SECRET", "pyramid_heroku.structlog": True}
        testapp = TestApp(app(settings))

        res = testapp.get("/hello", status=200)
        assert res.json == {"hello": "world"}

    logs.check(
        (
            "pyramid_mixpanel",
            "INFO",
            "consumer='PoliteBufferedConsumer' event='Mixpanel configured' "
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
                    "distinct_id": "foo-123",
                    "time": 1546300800,
                    "mp_lib": "python",
                    "$lib_version": "4.5.0",
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

    with LogCapture() as logs:
        settings = {"mixpanel.token": "SECRET", "pyramid_heroku.structlog": False}
        testapp = TestApp(app(settings))

        res = testapp.get("/hello", status=200)
        assert res.json == {"hello": "world"}

    logs.check(
        (
            "pyramid_mixpanel",
            "INFO",
            "Mixpanel configured consumer=PoliteBufferedConsumer, events=Events, "
            "event_properties=EventProperties, profile_properties=ProfileProperties, "
            "profile_meta_properties=ProfileMetaProperties",
        )
    )

    message = json_dumps(
        [
            {
                "event": "Page Viewed",
                "properties": {
                    "token": "SECRET",
                    "distinct_id": "foo-123",
                    "time": 1546300800,
                    "mp_lib": "python",
                    "$lib_version": "4.5.0",
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


@freeze_time("2019-01-01")
def test_header_event_props() -> None:
    """Test that event properties from header are added to the event."""
    with LogCapture() as logs:
        testapp = TestApp(app({"pyramid_heroku.structlog": True}))

        res = testapp.get(
            "/hello",
            headers={"X-Mixpanel-Title": "hello", "X-Mixpanel-Foo": "bar"},
            status=200,
        )
        assert res.json == {"hello": "world"}

    logs.check(
        (
            "pyramid_mixpanel",
            "INFO",
            "consumer='MockedConsumer' event='Mixpanel configured' "
            "event_properties='EventProperties' events='Events' "
            "profile_meta_properties='ProfileMetaProperties' "
            "profile_properties='ProfileProperties'",
        ),
        (
            "pyramid_mixpanel",
            "WARNING",
            "event='Mixpanel is in testing mode, no message will be sent!'",
        ),
        (
            "pyramid_mixpanel.track",
            "WARNING",
            "event=\"Property 'foo', from request header 'X-Mixpanel-Foo' is not a "
            'member of event_properties"',
        ),
    )

    assert res.app_request.mixpanel.api._consumer.flushed is True
    assert res.app_request.mixpanel.api._consumer.mocked_messages == [
        MockedMessage(
            endpoint="events",
            msg={
                "event": "Page Viewed",
                "properties": {
                    "token": "testing",
                    "distinct_id": "foo-123",
                    "time": 1546300800,
                    "mp_lib": "python",
                    "$lib_version": "4.5.0",
                    "Path": "/hello",
                    "Title": "hello",
                },
            },
        )
    ]

    with LogCapture() as logs:
        testapp = TestApp(app({}))

        res = testapp.get(
            "/hello",
            headers={"X-Mixpanel-Title": "hello", "X-Mixpanel-Foo": "bar"},
            status=200,
        )
        assert res.json == {"hello": "world"}

    logs.check(
        (
            "pyramid_mixpanel",
            "INFO",
            "Mixpanel configured consumer=MockedConsumer, events=Events, "
            "event_properties=EventProperties, profile_properties=ProfileProperties, "
            "profile_meta_properties=ProfileMetaProperties",
        ),
        (
            "pyramid_mixpanel",
            "WARNING",
            "Mixpanel is in testing mode, no message will be sent!",
        ),
        (
            "pyramid_mixpanel.track",
            "WARNING",
            "Property 'foo', from request header 'X-Mixpanel-Foo' is not a member of "
            "event_properties",
        ),
    )
    assert res.app_request.mixpanel.api._consumer.flushed is True
    assert res.app_request.mixpanel.api._consumer.mocked_messages == [
        MockedMessage(
            endpoint="events",
            msg={
                "event": "Page Viewed",
                "properties": {
                    "token": "testing",
                    "distinct_id": "foo-123",
                    "time": 1546300800,
                    "mp_lib": "python",
                    "$lib_version": "4.5.0",
                    "Path": "/hello",
                    "Title": "hello",
                },
            },
        )
    ]


@mock.patch("pyramid_mixpanel.consumer.PoliteBufferedConsumer.flush")
def test_request_mixpanel_not_used(flush: mock.MagicMock) -> None:
    """Test that flush() is not called if request.mixpanel was never called."""

    with LogCapture() as logs:
        settings = {"mixpanel.token": "SECRET", "pyramid_heroku.structlog": True}
        testapp = TestApp(app(settings))

        res = testapp.get("/bye", status=200)
        assert res.json == {"bye": "bye"}

    logs.check(
        (
            "pyramid_mixpanel",
            "INFO",
            "consumer='PoliteBufferedConsumer' event='Mixpanel configured' "
            "event_properties='EventProperties' events='Events' "
            "profile_meta_properties='ProfileMetaProperties' "
            "profile_properties='ProfileProperties'",
        )
    )
    flush.assert_not_called()
