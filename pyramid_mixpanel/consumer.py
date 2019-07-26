"""Consumers send events/profiles messages to Mixpanel's HTTP API."""

from dataclasses import dataclass
from dataclasses import field

import json
import typing as t


@dataclass(frozen=True)
class QueuedConsumer:
    """Queue sending Mixpanel messages in a separate background queue processor."""

    def send(self, endpoint: str, json_message: str) -> None:
        """Queue sending of Mixpanel message in a background task."""
        # send_api.delay(endpoint, json_message)
        raise NotImplementedError  # pragma: no cover


@dataclass(frozen=True)
class MockedMessage:
    """A single Mixpanel message stored by MockedConsumer."""

    endpoint: str
    msg: t.Dict["str", object]


@dataclass(frozen=True)
class MockedConsumer:
    """Save messages in an internal list, useful in unit testing."""

    # Internal storage of mocked message
    mocked_messages: t.List = field(default_factory=lambda: [])

    def send(self, endpoint: str, json_message: str) -> None:
        """Append message to the mocked_messages list."""
        msg = MockedMessage(endpoint=endpoint, msg=json.loads(json_message))
        self.mocked_messages.append(msg)
