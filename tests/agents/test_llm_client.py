"""LLM client tests — the Anthropic SDK is always mocked here; no real API
calls are made in the test suite.
"""

from unittest.mock import MagicMock, patch

from anthropic import APIError

from src.agents.llm_client import LLMClient, build_llm_client


def _fake_response(text: str):
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


@patch("src.agents.llm_client.Anthropic")
def test_generate_text_returns_stripped_completion(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    mock_client.messages.create.return_value = _fake_response("  hello there  ")

    client = LLMClient(api_key="key", model="claude-haiku-4-5-20251001")
    assert client.generate_text("system", "user") == "hello there"


@patch("src.agents.llm_client.Anthropic")
def test_generate_text_retries_once_then_returns_none(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    mock_client.messages.create.side_effect = APIError(
        message="boom", request=MagicMock(), body=None
    )

    client = LLMClient(api_key="key", model="claude-haiku-4-5-20251001")
    assert client.generate_text("system", "user") is None
    assert mock_client.messages.create.call_count == 2


@patch("src.agents.llm_client.Anthropic")
def test_generate_text_returns_none_on_empty_completion(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    mock_client.messages.create.return_value = _fake_response("   ")

    client = LLMClient(api_key="key", model="claude-haiku-4-5-20251001")
    assert client.generate_text("system", "user") is None


@patch("src.agents.llm_client.Anthropic")
def test_generate_json_parses_valid_json(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    mock_client.messages.create.return_value = _fake_response('{"estimate": [1, 2]}')

    client = LLMClient(api_key="key", model="claude-haiku-4-5-20251001")
    assert client.generate_json("system", "user") == {"estimate": [1, 2]}


@patch("src.agents.llm_client.Anthropic")
def test_generate_json_returns_none_on_malformed_json(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    mock_client.messages.create.return_value = _fake_response("not json at all")

    client = LLMClient(api_key="key", model="claude-haiku-4-5-20251001")
    assert client.generate_json("system", "user") is None


def test_build_llm_client_reads_model_from_config(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch("src.agents.llm_client.Anthropic"):
        client = build_llm_client({"llm": {"model": "claude-haiku-4-5-20251001"}})
    assert client._model == "claude-haiku-4-5-20251001"
