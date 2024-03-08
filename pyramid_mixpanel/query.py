"""Querying data from Mixpanel."""

import requests
import typing as t


class MultipleProfilesFoundException(ValueError):
    """Custom exception for multiple profiles."""

    def __init__(self, email, profile_ids):
        super().__init__(f"Multiple Mixpanel profiles found for email: {email}")
        self.email = email
        self.profile_ids = profile_ids

    def __str__(self):
        """Stringer method."""
        return f"{super().__str__()} - Profile IDs: {self.profile_ids}"


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
            raise MultipleProfilesFoundException(email, profiles)
