"""Tests for provided consumers."""

from pyramid_mixpanel.consumer import MockedConsumer
from pyramid_mixpanel.consumer import PoliteBufferedConsumer
from testfixtures import LogCapture
from unittest import mock
from urllib.error import URLError

import structlog


def test_MockedConsumer() -> None:
    """Test that MockedConsumer saves messages."""
    consumer = MockedConsumer()

    consumer.send(endpoint="events", json_message='{"foo":"Foo"}')
    consumer.send(endpoint="events", json_message='{"bar":"Bar"}')

    assert consumer.mocked_messages == [
        {"endpoint": "events", "msg": {"foo": "Foo"}},
        {"endpoint": "events", "msg": {"bar": "Bar"}},
    ]

    consumer.flush()
    assert consumer.flushed is True


def test_MockedConsumer_drop_system_properties() -> None:
    """Test that MockedConsumer saves messages."""
    PEOPLE_RAW = '{"$token": "testing", "$time": 1546300800, "$distinct_id": "foo-123", "$set": {"$name": "Bob"}}'  # noqa: E501
    EVENTS_RAW = '{"event": "Page Viewed", "properties": {"token": "testing", "distinct_id": "foo-123", "time": 1546300800, "$insert_id": "123e4567", "mp_lib": "python", "$lib_version": "4.9.0", "Path": "/hello"}}'  # noqa: E501

    # Default behaviour
    consumer = MockedConsumer()
    consumer.send(endpoint="people", json_message=PEOPLE_RAW)
    consumer.send(endpoint="events", json_message=EVENTS_RAW)

    assert consumer.mocked_messages == [
        {
            "endpoint": "people",
            "msg": {
                "$distinct_id": "foo-123",
                "$set": {
                    "$name": "Bob",
                },
            },
        },
        {
            "endpoint": "events",
            "msg": {
                "event": "Page Viewed",
                "properties": {
                    "distinct_id": "foo-123",
                    "Path": "/hello",
                },
            },
        },
    ]

    # Verbose behaviour
    consumer = MockedConsumer()
    consumer.DROP_SYSTEM_MESSAGE_PROPERTIES = False
    consumer.send(endpoint="people", json_message=PEOPLE_RAW)
    consumer.send(endpoint="events", json_message=EVENTS_RAW)

    assert consumer.mocked_messages == [
        {
            "endpoint": "people",
            "msg": {
                "$token": "testing",
                "$time": 1546300800,
                "$distinct_id": "foo-123",
                "$set": {"$name": "Bob"},
            },
        },
        {
            "endpoint": "events",
            "msg": {
                "event": "Page Viewed",
                "properties": {
                    "token": "testing",
                    "distinct_id": "foo-123",
                    "time": 1546300800,
                    "$insert_id": "123e4567",
                    "mp_lib": "python",
                    "$lib_version": "4.9.0",
                    "Path": "/hello",
                },
            },
        },
    ]


@mock.patch("mixpanel.BufferedConsumer.flush")
def test_PoliteBufferedConsumer(flush: mock.MagicMock) -> None:
    """Test that PoliteBufferedConsumer logs errors and continues."""
    structlog.configure(
        processors=[structlog.processors.KeyValueRenderer(sort_keys=True)],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    consumer = PoliteBufferedConsumer(use_structlog=True)

    consumer.send(endpoint="events", json_message='{"foo":"Foo"}')
    consumer.send(endpoint="events", json_message='{"bar":"Bar"}')

    assert consumer._buffers == {  # noqa: SF01
        "events": ['{"foo":"Foo"}', '{"bar":"Bar"}'],
        "people": [],
        "groups": [],
        "imports": [],
    }

    consumer.flush()
    flush.assert_called_with()

    with LogCapture() as logs:
        flush.side_effect = URLError("foo")
        consumer.flush()

    logs.check(
        (
            "pyramid_mixpanel.consumer",
            "ERROR",
            "event='It seems like Mixpanel is down.' exc_info=True",
        )
    )

    consumer = PoliteBufferedConsumer()
    with LogCapture() as logs:
        flush.side_effect = URLError("foo")
        consumer.flush()

    logs.check(
        ("pyramid_mixpanel.consumer", "ERROR", "It seems like Mixpanel is down.")
    )
