"""Consumers send events/profiles messages to Mixpanel's HTTP API."""

from dataclasses import dataclass
from dataclasses import field
from mixpanel import BufferedConsumer
from urllib.error import URLError

import json
import typing as t


@dataclass
class MockedConsumer:
    """Save messages in an internal list, useful in unit testing."""

    # Internal storage of mocked message
    mocked_messages: t.List = field(default_factory=lambda: [])

    # Drop message properties that are usually not needed in testing
    DROP_SYSTEM_MESSAGE_PROPERTIES: bool = True

    # True if .flush() was called
    flushed: bool = False

    def send(self, endpoint: str, json_message: str) -> None:
        """Append message to the mocked_messages list."""
        message = {
            "endpoint": endpoint,
            "msg": json.loads(json_message),
        }

        if self.DROP_SYSTEM_MESSAGE_PROPERTIES:
            # Events
            if "properties" in message["msg"]:
                message["msg"]["properties"].pop("$insert_id", None)  # type: ignore
                message["msg"]["properties"].pop("$lib_version", None)  # type: ignore
                message["msg"]["properties"].pop("mp_lib", None)  # type: ignore
                message["msg"]["properties"].pop("time", None)  # type: ignore
                message["msg"]["properties"].pop("token", None)  # type: ignore
            # Profiles
            else:
                message["msg"].pop("$token", None)
                message["msg"].pop("$time", None)

        self.mocked_messages.append(message)

    def flush(self, *args, **kwargs) -> None:
        """Set self.flushed to True."""
        self.flushed = True


class PoliteBufferedConsumer(BufferedConsumer):
    """Subclass of BufferedConsumer that logs network errors instead of failing.

    Inspired by:
    https://github.com/mixpanel/mixpanel-python/issues/36#issuecomment-72063207
    """

    def __init__(self, use_structlog: t.Optional[bool] = False, *args, **kwargs):
        """Initialize PoliteBufferedConsumer."""
        super().__init__(*args, **kwargs)
        self.use_structlog = use_structlog

    def flush(self, *args, **kwargs) -> None:
        """Try to send updates to Mixpanel."""
        try:
            super(PoliteBufferedConsumer, self).flush(*args, **kwargs)
        except URLError:
            if self.use_structlog:
                import structlog

                logger = structlog.get_logger(__name__)
                logger.exception("It seems like Mixpanel is down.", exc_info=True)
            else:
                import logging

                logger = logging.getLogger(__name__)
                logger.exception("It seems like Mixpanel is down.", exc_info=True)


@dataclass(frozen=True)
class QueuedConsumer:
    """Queue sending Mixpanel messages in a separate background queue processor."""

    def send(self, endpoint: str, json_message: str) -> None:
        """Queue sending of Mixpanel message in a background task."""
        # send_api.delay(endpoint, json_message)
        raise NotImplementedError  # pragma: no cover
