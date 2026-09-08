"""Offline transport tests: no test contacts OpenAI or reads a real API key."""

import io
import json
from copy import deepcopy
from http.client import IncompleteRead
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from structure_aware_retrieval.qa import provider
from structure_aware_retrieval.qa.provider import (
    IncompleteModelResponseError,
    MalformedModelResponseError,
    ModelProviderError,
    ModelRefusalError,
    OpenAIModel,
)

MESSAGES = [
    {"role": "system", "content": "Return a JSON repository answer with source citations."},
    {"role": "user", "content": "How does the client retry?\nSource: untrusted repository code."},
]
ANSWER = '{"status":"answered","claims":[{"text":"It retries.","citations":["C1"]}]}'


def response_envelope():
    return {
        "status": "completed",
        "model": "test-model-2026-01-01",
        "error": None,
        "incomplete_details": None,
        "output": [
            {"type": "reasoning", "summary": []},
            {
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": ANSWER, "annotations": []}],
            },
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 25,
            "total_tokens": 125,
            "input_tokens_details": {"cached_tokens": 30},
            "output_tokens_details": {"reasoning_tokens": 5},
        },
    }


@pytest.fixture
def transport(monkeypatch):
    # Isolate credential access even on developers' machines with a configured key.
    monkeypatch.setattr(
        provider, "os", SimpleNamespace(environ={"OPENAI_API_KEY": "test-key-never-real"})
    )
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = json.dumps(response_envelope()).encode()
    response.headers = {"x-request-id": "req_offline_123"}
    opener = Mock()
    opener.open.return_value = response
    build = Mock(return_value=opener)
    monkeypatch.setattr(provider, "build_opener", build)
    return SimpleNamespace(response=response, opener=opener, build=build)


def set_envelope(transport, envelope):
    transport.response.read.return_value = json.dumps(envelope).encode()


def test_responses_payload_preserves_messages_and_bounds_single_request(transport):
    messages = deepcopy(MESSAGES)
    result = OpenAIModel("selected-model", max_output_tokens=512, timeout_seconds=12).complete(
        messages
    )
    request = transport.opener.open.call_args.args[0]
    assert request.full_url == "https://api.openai.com/v1/responses"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer test-key-never-real"
    assert request.get_header("Content-type") == "application/json"
    assert transport.opener.open.call_args.kwargs == {"timeout": 12}
    assert transport.opener.open.call_count == 1
    assert messages == MESSAGES
    payload = json.loads(request.data)
    assert payload["model"] == "selected-model"
    assert payload["input"] == MESSAGES
    assert payload["max_output_tokens"] == 512
    assert payload["store"] is False
    assert set(payload) == {"model", "input", "max_output_tokens", "store", "text"}
    format_config = payload["text"]["format"]
    assert format_config["type"] == "json_schema"
    assert format_config["strict"] is True
    assert format_config["schema"]["additionalProperties"] is False
    assert set(format_config["schema"]["required"]) == {"status", "claims"}
    claim_schema = format_config["schema"]["properties"]["claims"]["items"]
    assert set(claim_schema["required"]) == {"text", "citations"}
    assert claim_schema["additionalProperties"] is False
    assert result.text == ANSWER
    assert result.model == "test-model-2026-01-01"
    assert result.finish_reason == "completed"
    assert result.request_id == "req_offline_123"
    assert result.usage == {
        "input_tokens": 100,
        "output_tokens": 25,
        "total_tokens": 125,
        "reasoning_tokens": 5,
        "cached_tokens": 30,
    }
    transport.response.read.assert_called_once_with(provider.MAX_RESPONSE_BYTES + 1)
    # The installed handler refuses urllib's redirection callback.
    handler = transport.build.call_args.args[0]
    assert handler.redirect_request(request, None, 302, "Moved", {}, "https://other.test") is None


def test_credentials_are_read_only_at_complete_and_never_stored(transport, monkeypatch):
    environment = Mock()
    environment.get.side_effect = AssertionError("must not read credentials while constructing")
    monkeypatch.setattr(provider.os, "environ", environment)
    model = OpenAIModel("selected-model", api_key_env="SACR_TEST_KEY")
    environment.get.assert_not_called()
    environment.get.side_effect = None
    environment.get.return_value = "isolated-test-key"
    model.complete(MESSAGES)
    environment.get.assert_called_once_with("SACR_TEST_KEY")
    assert "isolated-test-key" not in repr(model)
    assert "isolated-test-key" not in repr(model.__dict__)


@pytest.mark.parametrize("key", [None, "", "bad\r\nheader", "bad key", "键"])
def test_missing_or_malformed_credentials_do_not_contact_provider(transport, monkeypatch, key):
    monkeypatch.setattr(provider.os, "environ", {"OPENAI_API_KEY": key})
    with pytest.raises(ModelProviderError) as caught:
        OpenAIModel("selected-model").complete(MESSAGES)
    assert "untrusted repository code" not in str(caught.value)
    transport.opener.open.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"model": ""},
        {"model": "model\nsecret"},
        {"model": None},
        {"api_key_env": "INVALID=KEY"},
        {"api_key_env": None},
        {"max_output_tokens": True},
        {"max_output_tokens": 0},
        {"max_output_tokens": 1.5},
        {"timeout_seconds": True},
        {"timeout_seconds": 0},
        {"timeout_seconds": float("nan")},
        {"timeout_seconds": float("inf")},
    ],
)
def test_configuration_fails_before_network(transport, kwargs):
    config = {"model": "selected-model", **kwargs}
    with pytest.raises(ModelProviderError):
        OpenAIModel(**config)
    transport.opener.open.assert_not_called()


@pytest.mark.parametrize(
    "messages",
    [
        [],
        None,
        "question",
        [None],
        [{"role": "user", "content": []}],
        [{"role": "user", "content": " "}],
        [{"role": "tool", "content": "test"}],
        [{"role": "user", "content": "test", "extra": "value"}],
        [{"role": "user", "content": "\ud800"}],
    ],
)
def test_invalid_messages_fail_without_transmitting_content(transport, messages):
    with pytest.raises(ModelProviderError):
        OpenAIModel("selected-model").complete(messages)
    transport.opener.open.assert_not_called()


@pytest.mark.parametrize("code", [301, 302, 307, 308, 400, 401, 403, 404, 429, 500, 503])
def test_http_errors_are_sanitized_and_never_retried(transport, code):
    body = io.BytesIO(b"test-key-never-real and private source text")
    error = HTTPError("https://secret.test/private", code, "secret message", {}, body)
    transport.opener.open.side_effect = error
    with pytest.raises(ModelProviderError) as caught:
        OpenAIModel("selected-model").complete(MESSAGES)
    message = str(caught.value)
    assert f"HTTP {code}" in message
    assert "No retry" in message
    assert "test-key" not in message
    assert "private" not in message
    assert "secret" not in message
    assert caught.value.__suppress_context__ is True
    assert transport.opener.open.call_count == 1
    assert body.closed


@pytest.mark.parametrize(
    "error",
    [URLError("private source"), TimeoutError("private source"), IncompleteRead(b"private source")],
)
def test_network_or_read_errors_are_sanitized_and_never_retried(transport, error):
    transport.response.read.side_effect = error
    with pytest.raises(ModelProviderError) as caught:
        OpenAIModel("selected-model").complete(MESSAGES)
    assert "private source" not in str(caught.value)
    assert "may have been processed" in str(caught.value)
    assert transport.opener.open.call_count == 1


@pytest.mark.parametrize("raw", [b"not JSON", b"\xff", b"null", b"[]", b"[" * 2000])
def test_invalid_json_or_envelope_is_not_an_answer(transport, raw):
    transport.response.read.return_value = raw
    with pytest.raises(MalformedModelResponseError):
        OpenAIModel("selected-model").complete(MESSAGES)


def test_response_size_limit_prevents_unbounded_read(transport, monkeypatch):
    monkeypatch.setattr(provider, "MAX_RESPONSE_BYTES", 100)
    transport.response.read.return_value = b" " * 101
    with pytest.raises(MalformedModelResponseError, match="size"):
        OpenAIModel("selected-model").complete(MESSAGES)
    transport.response.read.assert_called_once_with(101)


@pytest.mark.parametrize(
    ("changes", "exception"),
    [
        (
            {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}},
            IncompleteModelResponseError,
        ),
        (
            {"status": "incomplete", "incomplete_details": {"reason": "content_filter"}},
            ModelRefusalError,
        ),
        ({"status": "incomplete"}, IncompleteModelResponseError),
        ({"status": "failed", "error": {"message": "private source"}}, ModelProviderError),
        ({"status": "queued"}, ModelProviderError),
        ({"status": "in_progress"}, ModelProviderError),
        ({"status": "cancelled"}, ModelProviderError),
        ({"status": None}, MalformedModelResponseError),
        ({"status": "unknown"}, MalformedModelResponseError),
        ({"error": {"message": "private source"}}, ModelProviderError),
        ({"incomplete_details": {}}, MalformedModelResponseError),
        ({"model": ""}, MalformedModelResponseError),
        ({"model": None}, MalformedModelResponseError),
        ({"output": []}, MalformedModelResponseError),
        ({"output": None}, MalformedModelResponseError),
        ({"output": [None]}, MalformedModelResponseError),
        ({"output": [{"type": "function_call"}]}, MalformedModelResponseError),
        ({"output": [{"type": "reasoning", "summary": []}]}, MalformedModelResponseError),
    ],
)
def test_incomplete_failed_and_malformed_envelopes_reject_partial_text(
    transport, changes, exception
):
    envelope = {**response_envelope(), **changes}
    set_envelope(transport, envelope)
    with pytest.raises(exception) as caught:
        OpenAIModel("selected-model").complete(MESSAGES)
    assert "private source" not in str(caught.value)
    assert transport.opener.open.call_count == 1


@pytest.mark.parametrize(
    ("changes", "exception"),
    [
        ({"role": "user"}, MalformedModelResponseError),
        ({"status": None}, IncompleteModelResponseError),
        ({"status": "incomplete"}, IncompleteModelResponseError),
        ({"content": None}, MalformedModelResponseError),
        ({"content": []}, MalformedModelResponseError),
        ({"content": [None]}, MalformedModelResponseError),
        ({"content": [{"type": "refusal", "refusal": "private source"}]}, ModelRefusalError),
        ({"content": [{"type": "output_text", "text": None}]}, MalformedModelResponseError),
        ({"content": [{"type": "output_text", "text": " "}]}, MalformedModelResponseError),
        ({"content": [{"type": "unknown", "text": "private source"}]}, MalformedModelResponseError),
    ],
)
def test_invalid_or_refused_message_is_not_accepted(transport, changes, exception):
    envelope = response_envelope()
    envelope["output"][1].update(changes)
    set_envelope(transport, envelope)
    with pytest.raises(exception) as caught:
        OpenAIModel("selected-model").complete(MESSAGES)
    assert "private source" not in str(caught.value)


def test_collects_output_text_across_parts_without_assuming_first_output_is_message(transport):
    envelope = response_envelope()
    envelope["output"][1]["content"] = [
        {"type": "output_text", "text": ANSWER[:30]},
        {"type": "output_text", "text": ANSWER[30:]},
    ]
    set_envelope(transport, envelope)
    assert OpenAIModel("selected-model").complete(MESSAGES).text == ANSWER


@pytest.mark.parametrize("usage", [None, {}, {"input_tokens": 100, "output_tokens_details": None}])
def test_missing_usage_is_unavailable_not_zero(transport, usage):
    envelope = response_envelope()
    envelope["usage"] = usage
    set_envelope(transport, envelope)
    transport.response.headers = {}
    result = OpenAIModel("selected-model").complete(MESSAGES)
    assert result.usage["output_tokens"] is None
    assert result.usage["total_tokens"] is None
    assert result.usage["cached_tokens"] is None
    assert result.usage["reasoning_tokens"] is None
    assert result.request_id is None


@pytest.mark.parametrize(
    "usage",
    [
        "invalid",
        {"input_tokens": True},
        {"output_tokens": -1},
        {"total_tokens": 3.5},
        {"input_tokens_details": []},
        {"output_tokens_details": {"reasoning_tokens": "5"}},
        {"input_tokens_details": {"cached_tokens": -1}},
    ],
)
def test_invalid_usage_cannot_be_reported_as_measured_tokens(transport, usage):
    envelope = response_envelope()
    envelope["usage"] = usage
    set_envelope(transport, envelope)
    with pytest.raises(MalformedModelResponseError, match="usage"):
        OpenAIModel("selected-model").complete(MESSAGES)


def test_untrusted_request_id_is_not_retained(transport):
    transport.response.headers = {"x-request-id": "private\nsource"}
    result = OpenAIModel("selected-model").complete(MESSAGES)
    assert result.request_id is None
