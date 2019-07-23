"""Integration with Mixpanel.

There are two things you can do:
* Send user interaction events or set profile properties via MixpanelTrack.
* Query for events and profiles via MixpanelQuery.

MixpanelTrack is prepared as `request.mixpanel` for easier usage in view code.
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from mixpanel import Mixpanel
from pyramid.config import Configurator
from pyramid.request import Request

import json
import requests
import structlog
import typing as t

logger = structlog.get_logger(__name__)


class Events(Enum):
    page_viewed = "Page Viewed"
    button_link_clicked = "Button/Link Clicked"
    user_signed_up = "User Signed Up"
    user_logged_in = "User Logged In"
    user_charged = "User Charged"
    user_disabled = "User Disabled"


class EventProperties(Enum):
    title = "Title"
    path = "Path"


class ProfileProperties(Enum):
    dollar_created = "$created"
    dollar_email = "$email"
    state = "State"


#################################################
#              ---- Tracking ----               #
# Utilities for tracking user actions handlers. #
#################################################


class MixpanelTrack:
    """Wrapper around the official `mixpanel` server-side integration of Mixpanel.

    You can track events and/or set people profiles. Uses
    https://pypi.python.org/pypi/mixpanel under the hood.
    """

    # Add typing for user, possibly with
    # https://mypy.readthedocs.io/en/latest/protocols.html#simple-user-defined-protocols
    def __init__(self, user, settings: t.Dict[str, str]) -> None:
        """Initialize API connector."""
        if settings.get("mixpanel.testing"):
            self.api = Mixpanel(token="token", consumer=MockedConsumer())  # nosec
        else:
            self.api = Mixpanel(
                token=settings["mixpanel.token"], consumer=QueuedConsumer()
            )

        self.user = user

    def track(self, event_name: str, props: t.Optional[dict] = None) -> None:
        """Track a Mixpanel event."""

        if event_name not in ProfileProperties.__members__:
            raise Exception(f"Unknown Mixpanel event: {event_name}")

        if not props:
            props = {}

        self.api.track(self.user.distinct_id, event_name, props)

    def profile_sync(
        self, extra: t.Optional[dict] = None, meta: t.Optional[dict] = None
    ) -> None:
        """Create or update user's Profile.

        The `meta` argument overrides Mixpanel special properties, such as $ip.
        """
        user_data = {
            ProfileProperties["dollar_email"].value: self.user.email,
            ProfileProperties["dollar_created"].value: self.user.created.isoformat(),
            ProfileProperties["state"].value: self.user.state,
        }
        if extra:
            user_data.update(extra)

        self.profile_set(user_data, meta=meta)

    def profile_set(self, props: dict, meta: t.Optional[dict] = None) -> None:
        """Set properties to a Profile.

        This creates a profile if one does not yet exist.

        Use `meta` to override are Mixpanel special properties, such as $ip.
        """
        if not meta:
            meta = {}

        self.api.people_set(self.user.distinct_id, props, meta)

    def profile_increment(self, props: dict) -> None:
        """Wrap around api.people_increment to set distinct_id."""
        self.api.people_increment(self.user.distinct_id, props)

    def profile_track_charge(self, amount: int, props: dict) -> None:
        """Wrap around api.people_track_charge to set distinct_id."""
        self.api.people_track_charge(self.user.distinct_id, amount, props)


@dataclass(frozen=True)
class QueuedConsumer:
    """Queue sending Mixpanel messages in a separate background queue processor."""

    def send(self, endpoint, json_message):
        """Queue sending of Mixpanel message in a background task."""
        # send_api.delay(endpoint, json_message)
        raise NotImplementedError


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

    def send(self, endpoint, json_message):
        """Append message to the mocked_messages list."""
        msg = MockedMessage(endpoint=endpoint, msg=json.loads(json_message))
        self.mocked_messages.append(msg)


def mixpanel_track(request: Request):
    """Return MixpanelTrack class instance."""
    return MixpanelTrack(settings=request.registry.settings, user=request.user)


def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    config.add_request_method(mixpanel_track, "mixpanel", reify=True)


##############################################
#          ---- Data Querying ----           #
# Utilities for querying data from Mixpanel. #
##############################################


class MixpanelQuery(object):
    """Query Mixpanel for events and profiles.

    You can use one of the pre-built queries, or provide your own.
    """

    ENDPOINT = "https://mixpanel.com/api/2.0/jql"

    def __init__(self, settings: t.Dict[str, str]) -> None:
        """Save API credentials."""
        self.api_secret = settings["mixpanel.api_secret"]

    def jql(self, jql: str) -> t.List[t.Dict]:
        """Query Mixpanel using JQL script.

        You can troubleshoot the script on
        https://mixpanel.com/report/<PROJECT_ID>/jql-console.
        """
        resp = requests.post(
            self.ENDPOINT, auth=(self.api_secret, ""), data={"script": jql}
        )
        resp.raise_for_status()
        return resp.json()

    #################################################
    #         ---- Pre-built queries ----           #
    # A couple of queries that we use all the time. #
    #################################################

    def profile_by_email(self, email: str):
        """Return a Mixpanel profile by given email."""
        profiles = self.jql(
            """
            function main() {
              return People(
              )
              .filter(function(profile) {
                return profile.properties.$email == '%(email)s';
              })
              .map(function(profile) {
                return {
                  distinct_id: profile.distinct_id,
                  email: profile.properties.$email,
                };
              });
            }
        """
            % {"email": email}
        )

        if len(profiles) == 0:
            return None
        elif len(profiles) == 1:
            return profiles[0]
        else:
            raise ValueError(
                f"Found more than one Profile for email '{email}': "
                f"{[profile['distinct_id'] for profile in profiles]}"
            )
