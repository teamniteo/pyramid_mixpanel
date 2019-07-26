"""Tests for querying data from Mixpanel."""

from pyramid_mixpanel.query import MixpanelQuery

import pytest
import responses

SETTINGS = {"mixpanel.api_secret": "bar"}


@responses.activate
def test_zero_results() -> None:
    """Return None if no profiles found."""
    responses.add(
        responses.POST, "https://mixpanel.com/api/2.0/jql", json=[], status=200
    )

    assert MixpanelQuery(SETTINGS).profile_by_email("foo") is None


@responses.activate
def test_too_many_results() -> None:
    """Raise exception if more than one profiles found."""
    responses.add(
        responses.POST,
        "https://mixpanel.com/api/2.0/jql",
        json=[
            {"distinct_id": "one", "email": "foo@bar.com"},
            {"distinct_id": "two", "email": "foo@bar.com"},
        ],
        status=200,
    )

    with pytest.raises(ValueError) as cm:
        MixpanelQuery(SETTINGS).profile_by_email("foo@bar.com")

    assert (
        str(cm.value)
        == "Found more than one Profile for email 'foo@bar.com': ['one', 'two']"
    )


@responses.activate
def test_profile_by_email() -> None:
    """Test happy path."""
    responses.add(
        responses.POST,
        "https://mixpanel.com/api/2.0/jql",
        json=[{"distinct_id": "foo", "email": "foo@bar.com"}],
        status=200,
    )

    assert MixpanelQuery(SETTINGS).profile_by_email("foo@bar.com") == {
        "distinct_id": "foo",
        "email": "foo@bar.com",
    }
