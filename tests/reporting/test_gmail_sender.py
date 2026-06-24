"""send_report's Gmail call is always mocked here — no real OAuth/network.
Asserts the email body is exactly the JSON payload (no surrounding prose)
and that the send call happens exactly once per report.
"""

import base64
import json
from unittest.mock import MagicMock, patch

from src.reporting.gmail_sender import _load_credentials, send_report

_PAYLOAD = {
    "group_name": "Team-Alpha",
    "students": ["Jane Doe"],
    "github_repo": "https://github.com/team-alpha/marl-copthief",
    "cop_mcp_url": "https://cop-mcp-alpha.example.com",
    "thief_mcp_url": "https://thief-mcp-alpha.example.com",
    "timezone": "Asia/Jerusalem",
    "sub_games": [{"winner": "cop"}],
    "totals": {"cop": 90, "thief": 40},
}


@patch("src.reporting.gmail_sender.build")
@patch("src.reporting.gmail_sender._load_credentials")
def test_send_report_body_is_exactly_the_json_payload(mock_load_credentials, mock_build):
    mock_load_credentials.return_value = MagicMock()
    mock_send = MagicMock()
    mock_send.execute.return_value = {"id": "msg-123"}
    mock_build.return_value.users.return_value.messages.return_value.send.return_value = mock_send

    response = send_report(
        _PAYLOAD, "rmisegal+uoh26b@gmail.com",
        client_secret_path="secrets/client_secret.json", token_path="secrets/token.json",
    )

    assert response == {"id": "msg-123"}
    mock_send.execute.assert_called_once()

    sent_body = mock_build.return_value.users.return_value.messages.return_value.send.call_args.kwargs["body"]
    raw_message = base64.urlsafe_b64decode(sent_body["raw"]).decode()
    message_body = raw_message.split("\n\n", 1)[1]
    assert json.loads(message_body) == _PAYLOAD


@patch("src.reporting.gmail_sender.build")
@patch("src.reporting.gmail_sender._load_credentials")
def test_send_report_sends_to_the_given_recipient(mock_load_credentials, mock_build):
    mock_load_credentials.return_value = MagicMock()
    mock_send = MagicMock()
    mock_send.execute.return_value = {"id": "msg-456"}
    mock_build.return_value.users.return_value.messages.return_value.send.return_value = mock_send

    send_report(
        _PAYLOAD, "rmisegal+uoh26b@gmail.com",
        client_secret_path="secrets/client_secret.json", token_path="secrets/token.json",
    )

    sent_body = mock_build.return_value.users.return_value.messages.return_value.send.call_args.kwargs["body"]
    raw_message = base64.urlsafe_b64decode(sent_body["raw"]).decode()
    assert "rmisegal+uoh26b@gmail.com" in raw_message.split("\n\n", 1)[0]


@patch("src.reporting.gmail_sender.Credentials")
def test_load_credentials_reuses_a_cached_valid_token_with_no_refresh_or_flow(mock_credentials_cls, tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text("{}")
    cached = MagicMock(valid=True)
    mock_credentials_cls.from_authorized_user_file.return_value = cached

    creds = _load_credentials(tmp_path / "client_secret.json", token_path)

    assert creds is cached
    cached.refresh.assert_not_called()


@patch("src.reporting.gmail_sender.Request")
@patch("src.reporting.gmail_sender.Credentials")
def test_load_credentials_refreshes_an_expired_token_in_place(mock_credentials_cls, mock_request, tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text("{}")
    expired = MagicMock(valid=False, expired=True, refresh_token="rt")
    expired.to_json.return_value = "{\"refreshed\": true}"
    mock_credentials_cls.from_authorized_user_file.return_value = expired

    creds = _load_credentials(tmp_path / "client_secret.json", token_path)

    assert creds is expired
    expired.refresh.assert_called_once_with(mock_request.return_value)
    assert token_path.read_text() == "{\"refreshed\": true}"


@patch("src.reporting.gmail_sender.InstalledAppFlow")
@patch("src.reporting.gmail_sender.Credentials")
def test_load_credentials_runs_the_interactive_flow_when_no_cached_token_exists(
    mock_credentials_cls, mock_flow_cls, tmp_path,
):
    token_path = tmp_path / "token.json"  # does not exist yet
    fresh = MagicMock()
    fresh.to_json.return_value = "{\"fresh\": true}"
    mock_flow_cls.from_client_secrets_file.return_value.run_local_server.return_value = fresh

    creds = _load_credentials(tmp_path / "client_secret.json", token_path)

    assert creds is fresh
    mock_credentials_cls.from_authorized_user_file.assert_not_called()
    assert token_path.read_text() == "{\"fresh\": true}"
