# Mini-PRD — Email Reporting

## Description / theoretical background

After all 6 sub-games of a series complete, the Cop agent automatically
triggers a single summary email to the grading address, using the Gmail
API with OAuth token-based auth (preferred over username/password since a
stolen short-lived token has limited value). The email body is the
Internal Game JSON only — no free text — so the grading system can ingest
it automatically.

## Requirements, inputs/outputs

- **Input:** the completed series' results (per-sub-game outcomes, scores,
  URLs, group metadata) plus `config.yaml: reporting.recipient_email`.
- **Output:** one email sent to `rmisegal+uoh26b@gmail.com`, body = the
  Internal Game JSON (§11.1 of the requirements) serialized exactly, no
  surrounding prose or markdown.
- **Auth input:** OAuth client secret + token paths from `.env`
  (`GMAIL_CLIENT_SECRET_PATH`, `GMAIL_TOKEN_PATH`), obtained via a Google
  Cloud project per the course's recorded walkthrough.

## Algorithm

1. After sub-game 6 completes (and is valid — see Technical Loss below),
   assemble the Internal Game JSON from the engine's accumulated results.
2. Validate the JSON against the schema in `hw06_requirements.md` §11.1
   before sending (a test enforces this).
3. Authenticate to Gmail API using the stored OAuth token (refresh if
   expired).
4. Send the email with the JSON as the entire body; log the send
   confirmation to `results/`.

## Constraints and limitations, alternatives considered

- **Technical Loss handling:** if a sub-game fails to complete due to a
  technical fault (e.g. MCP server unreachable, malformed tool response),
  it is voided and automatically re-run so the series ends with exactly 6
  valid sub-games before the email is sent.
- **Alternative considered:** SMTP with a regular mailbox password —
  rejected per the assignment's explicit preference for token-based auth
  with revocability.

## Edge cases

- Gmail API rate-limited or temporarily down at send time — retry with
  backoff; do not silently drop the report.
- OAuth token expired and refresh fails — surface a clear error rather than
  sending a malformed/partial report.
- A sub-game technical-loss loop that never resolves (e.g. persistent
  server outage) — cap re-run attempts and log a clear failure rather than
  looping forever.

## Success criteria / test scenarios

- A test mocks the Gmail send call and asserts the JSON payload matches the
  required schema exactly (keys, types, structure).
- A manual/integration run confirms a real email arrives with only the JSON
  as the body.
- A simulated technical loss correctly triggers exactly one re-run of that
  sub-game, not a duplicate of the whole series.
