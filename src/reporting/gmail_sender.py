"""Sends the Internal Game JSON report via the Gmail API.

OAuth credentials are never committed: the client secret and cached token
live wherever `GMAIL_CLIENT_SECRET_PATH` / `GMAIL_TOKEN_PATH` (`.env`)
point, owned by the user's own Google Cloud project per
docs/prd/email-reporting.md. The very first run on a machine with no
cached token opens an interactive browser consent flow
(`InstalledAppFlow.run_local_server`) — every run after that reuses/
refreshes the cached token with no further interaction.
"""

import base64
import json
import os
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
_SUBJECT = "HW06 Cops and Thieves -- Internal Game JSON Report"


def _load_credentials(client_secret_path: Path, token_path: Path) -> Credentials:
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), _SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    return creds


def send_report(
    payload: dict,
    recipient: str,
    client_secret_path: Path | str | None = None,
    token_path: Path | str | None = None,
    subject: str = _SUBJECT,
) -> dict:
    """Send `payload` as the entire email body — no surrounding prose — to
    `recipient`. Caller is responsible for schema-validating `payload`
    first (`src.reporting.schema.validate_internal_game_json`, or
    `src.reporting.bonus_schema.validate_bonus_game_json` for a Phase 7
    bonus report — pass a distinguishing `subject` in that case). Returns
    the Gmail API's send response (contains the sent message id), for
    logging.
    """
    client_secret_path = Path(client_secret_path or os.environ["GMAIL_CLIENT_SECRET_PATH"])
    token_path = Path(token_path or os.environ["GMAIL_TOKEN_PATH"])

    creds = _load_credentials(client_secret_path, token_path)
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(json.dumps(payload, indent=2))
    message["to"] = recipient
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    return service.users().messages().send(userId="me", body={"raw": raw}).execute()
