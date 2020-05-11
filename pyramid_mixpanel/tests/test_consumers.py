"""Tests for provided consumers."""

from pyramid_mixpanel.consumer import MockedConsumer
from pyramid_mixpanel.consumer import MockedMessage
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

    assert len(consumer.mocked_messages) == 2
    assert consumer.mocked_messages[0] == MockedMessage("events", {"foo": "Foo"})
    assert consumer.mocked_messages[1] == MockedMessage("events", {"bar": "Bar"})

    consumer.flush()
    assert consumer.flushed is True


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
