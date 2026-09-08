"""A single-request OpenAI Responses adapter with no implicit model or retries."""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from http.client import HTTPException
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

RESPONSES_URL = "https://api.openai.com/v1/responses"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_SCHEMA_BYTES = 256 * 1024
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["answered", "insufficient_context"]},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "citations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "citations"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["status", "claims"],
    "additionalProperties": False,
}


class ModelProviderError(ValueError):
    """A sanitized provider failure; request text and credentials are never included."""

    def __init__(self, *args, response_metadata: dict | None = None):
        super().__init__(*args)
        # Metadata is explicit archival data, never part of exception text/arguments.
        self.response_metadata = response_metadata


class ModelRefusalError(ModelProviderError):
    """The provider declined the request instead of returning an answer."""


class IncompleteModelResponseError(ModelProviderError):
    """Generation did not complete; partial content is not an answer."""


class MalformedModelResponseError(ModelProviderError):
    """The provider returned an invalid or unsupported response envelope."""


@dataclass(frozen=True)
class ModelResponse:
    """Raw answer text and provider-reported metadata, before citation validation."""

    text: str
    model: str
    usage: dict[str, int | None]
    request_id: str | None = None
    finish_reason: str | None = None
    raw_response: dict | None = None
    response_id: str | None = None
    model_revision: str | None = None


class AnswerModel(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> ModelResponse:
        """Generate one answer from already prepared messages."""
        ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Returning None makes urllib raise HTTPError without forwarding Authorization.
        return None


@dataclass(frozen=True)
class OpenAIModel:
    """Send one bounded, non-streaming request to the fixed OpenAI API endpoint.

    Constructing this object is offline. Only ``complete`` reads the configured
    environment variable. Error messages never expose response bodies or request content.
    Bounded JSON responses remain available as explicit archival metadata.
    An unsuccessful attempt is never automatically retried and may have been billed.
    """

    model: str
    api_key_env: str = "OPENAI_API_KEY"
    max_output_tokens: int = 1024
    timeout_seconds: float = 60
    output_schema: dict | None = None
    schema_name: str = "repository_answer"
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        if not _identifier(self.model):
            raise ModelProviderError("Set an explicit, valid OpenAI model ID.")
        if not isinstance(self.api_key_env, str) or not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*", self.api_key_env
        ):
            raise ModelProviderError("API key environment variable name is invalid.")
        if type(self.max_output_tokens) is not int or self.max_output_tokens <= 0:
            raise ModelProviderError("max_output_tokens must be a positive integer.")
        if (
            type(self.timeout_seconds) not in (int, float)
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise ModelProviderError("timeout_seconds must be a positive finite number.")
        if not isinstance(self.schema_name, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,64}", self.schema_name
        ):
            raise ModelProviderError("Structured output schema_name is invalid.")
        if self.reasoning_effort is not None and self.reasoning_effort not in (
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
        ):
            raise ModelProviderError("Unsupported reasoning_effort setting.")
        if self.output_schema is not None:
            object.__setattr__(self, "output_schema", _schema_copy(self.output_schema))

    def request_payload(self, messages: list[dict[str, str]]) -> dict:
        """Build exact request settings offline, excluding credentials and transport headers."""
        _validate_messages(messages)
        payload = {
            "model": self.model,
            "input": messages,
            "max_output_tokens": self.max_output_tokens,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": self.schema_name,
                    "strict": True,
                    "schema": _schema_copy(
                        ANSWER_SCHEMA if self.output_schema is None else self.output_schema
                    ),
                }
            },
        }
        if self.reasoning_effort is not None:
            payload["reasoning"] = {"effort": self.reasoning_effort}
        try:
            # Round-trip gives the caller an independent, serializable frozen candidate.
            body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            return json.loads(body)
        except (TypeError, ValueError, UnicodeError, RecursionError):
            raise ModelProviderError("Messages must contain valid Unicode text.") from None

    def complete(self, messages: list[dict[str, str]]) -> ModelResponse:
        """Call the Responses API once; validate its envelope, not answer semantics."""
        payload = self.request_payload(messages)
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ModelProviderError(
                f"Set {self.api_key_env} in your environment before generating an answer."
            )
        if not re.fullmatch(r"[!-~]+", key):
            raise ModelProviderError("The configured API key contains invalid characters.")
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        request = Request(
            RESPONSES_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        request_id = None
        try:
            with build_opener(_NoRedirect()).open(
                request, timeout=self.timeout_seconds
            ) as response:
                request_id = response.headers.get("x-request-id")
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as error:
            code = error.code
            request_id = error.headers.get("x-request-id") if error.headers else None
            error.close()
            raise ModelProviderError(
                _http_error_message(code), response_metadata=_response_metadata(None, request_id)
            ) from None
        except (URLError, OSError, HTTPException):
            raise ModelProviderError(
                "OpenAI request failed or timed out; check connectivity. No retry was made. "
                "The request may have been processed.",
                response_metadata=_response_metadata(None, request_id),
            ) from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise MalformedModelResponseError(
                "OpenAI response exceeded the allowed size.",
                response_metadata=_response_metadata(None, request_id),
            )
        try:
            envelope = json.loads(
                raw, object_pairs_hook=_json_object, parse_constant=_json_constant
            )
        except (ValueError, UnicodeError, RecursionError):
            raise MalformedModelResponseError(
                "OpenAI returned invalid JSON.",
                response_metadata=_response_metadata(None, request_id),
            ) from None
        return _parse_response(envelope, request_id)


def _json_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def _json_constant(_value: str) -> None:
    raise ValueError("Nonfinite JSON value")


def _schema_copy(schema: object) -> dict:
    if not isinstance(schema, dict) or not schema:
        raise ModelProviderError("output_schema must be a nonempty JSON object.")
    try:
        encoded = json.dumps(schema, ensure_ascii=False, allow_nan=False).encode("utf-8")
        copied = json.loads(encoded, object_pairs_hook=_json_object)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ModelProviderError("output_schema must contain valid JSON and Unicode.") from None
    if len(encoded) > MAX_SCHEMA_BYTES:
        raise ModelProviderError("output_schema exceeds the allowed size.")
    return copied


def _identifier(value: object) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}", value)
    )


def _validate_messages(messages: object) -> None:
    if not isinstance(messages, list) or not messages:
        raise ModelProviderError("Provide a nonempty list of text messages.")
    for message in messages:
        if (
            not isinstance(message, dict)
            or set(message) != {"role", "content"}
            or message["role"] not in ("system", "developer", "user", "assistant")
            or not isinstance(message["content"], str)
            or not message["content"].strip()
        ):
            raise ModelProviderError("Each message must have a supported role and nonempty text.")


def _http_error_message(code: int) -> str:
    if code in (401, 403):
        action = "Check the API key and project/model permissions."
    elif code == 429:
        action = "Check API quota and rate limits before another attempt."
    elif code == 404:
        action = "Check the selected model ID and API access."
    elif 300 <= code < 400:
        action = "Redirects are disabled; use the official OpenAI API endpoint."
    elif code >= 500:
        action = "The service failed; check provider status before another attempt."
    else:
        action = "Check model support for Responses, structured outputs, and the token limit."
    return f"OpenAI request failed (HTTP {code}). {action} No retry was made."


def _parse_response(envelope: object, request_id: object) -> ModelResponse:
    metadata = _response_metadata(envelope, request_id)
    try:
        return _validated_response(envelope, metadata)
    except ModelProviderError as error:
        error.response_metadata = metadata
        raise


def _validated_response(envelope: object, metadata: dict) -> ModelResponse:
    if not isinstance(envelope, dict):
        raise MalformedModelResponseError("OpenAI response must be an object.")
    status = envelope.get("status")
    if status == "incomplete":
        details = envelope.get("incomplete_details")
        reason = details.get("reason") if isinstance(details, dict) else None
        if reason == "content_filter":
            raise ModelRefusalError("OpenAI declined the request; no answer was accepted.")
        if reason == "max_output_tokens":
            raise IncompleteModelResponseError(
                "OpenAI reached max_output_tokens; review the output budget before another attempt."
            )
        raise IncompleteModelResponseError(
            "OpenAI returned incomplete output; no answer was accepted."
        )
    if (
        status in ("failed", "cancelled", "queued", "in_progress")
        or envelope.get("error") is not None
    ):
        raise ModelProviderError("OpenAI did not complete generation; no retry was made.")
    if status != "completed" or envelope.get("incomplete_details") is not None:
        raise MalformedModelResponseError("OpenAI response has an invalid completion status.")
    model = envelope.get("model")
    if not _identifier(model):
        raise MalformedModelResponseError("OpenAI response is missing a valid reported model ID.")
    output = envelope.get("output")
    if not isinstance(output, list) or not output:
        raise MalformedModelResponseError("OpenAI response is missing assistant output.")
    texts = []
    for item in output:
        if not isinstance(item, dict):
            raise MalformedModelResponseError("OpenAI response contains an invalid output item.")
        if item.get("type") == "reasoning":
            continue
        if item.get("type") != "message" or item.get("role") != "assistant":
            raise MalformedModelResponseError("OpenAI returned an unsupported output item.")
        if item.get("status") != "completed":
            raise IncompleteModelResponseError("OpenAI returned an incomplete assistant message.")
        content = item.get("content")
        if not isinstance(content, list) or not content:
            raise MalformedModelResponseError("OpenAI response is missing message content.")
        for part in content:
            if not isinstance(part, dict):
                raise MalformedModelResponseError(
                    "OpenAI response contains invalid message content."
                )
            if part.get("type") == "refusal":
                raise ModelRefusalError("OpenAI declined the request; no answer was accepted.")
            if part.get("type") != "output_text" or not isinstance(part.get("text"), str):
                raise MalformedModelResponseError("OpenAI response contains unsupported content.")
            texts.append(part["text"])
    text = "".join(texts)
    if not text.strip():
        raise MalformedModelResponseError("OpenAI returned empty answer text.")
    try:
        text.encode("utf-8")
    except UnicodeError:
        raise MalformedModelResponseError("OpenAI returned invalid Unicode answer text.") from None
    return ModelResponse(
        text=text,
        model=model,
        usage=_parse_usage(envelope.get("usage")),
        request_id=metadata["request_id"],
        finish_reason="completed",
        raw_response=metadata["raw_response"],
        response_id=metadata["response_id"],
        model_revision=metadata["model_revision"],
    )


def _response_metadata(envelope: object, request_id: object) -> dict:
    """Retain bounded JSON/known usage even when no successful answer is accepted."""
    raw_response = None
    if isinstance(envelope, dict):
        try:
            encoded = json.dumps(
                envelope, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
            if len(encoded) <= MAX_RESPONSE_BYTES:
                raw_response = json.loads(encoded)
        except (TypeError, ValueError, UnicodeError, RecursionError):
            pass
    source = raw_response or {}
    try:
        usage = _parse_usage(source.get("usage"))
    except ModelProviderError:
        usage = _parse_usage(None)
    texts = []
    output = source.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict) or item.get("role") != "assistant":
                continue
            content = item.get("content")
            if item.get("type") != "message" or not isinstance(content, list):
                continue
            for part in content:
                if (
                    isinstance(part, dict)
                    and part.get("type") == "output_text"
                    and isinstance(part.get("text"), str)
                ):
                    texts.append(part["text"])
    status = source.get("status")
    return {
        "text": "".join(texts) if texts else None,
        "model": source.get("model") if _identifier(source.get("model")) else None,
        "usage": usage,
        "request_id": request_id if _identifier(request_id) else None,
        "finish_reason": status
        if status in ("completed", "incomplete", "failed", "cancelled", "queued", "in_progress")
        else None,
        "raw_response": raw_response,
        "response_id": source.get("id") if _identifier(source.get("id")) else None,
        "model_revision": source.get("model_revision")
        if _identifier(source.get("model_revision"))
        else None,
    }


def _parse_usage(usage: object) -> dict[str, int | None]:
    if usage is None:
        usage = {}
    if not isinstance(usage, dict):
        raise MalformedModelResponseError("OpenAI response has invalid usage metadata.")
    counters = {name: usage.get(name) for name in ("input_tokens", "output_tokens", "total_tokens")}
    for field, counter in (
        ("input_tokens_details", "cached_tokens"),
        ("output_tokens_details", "reasoning_tokens"),
    ):
        details = usage.get(field)
        if details is None:
            details = {}
        if not isinstance(details, dict):
            raise MalformedModelResponseError("OpenAI response has invalid usage metadata.")
        counters[counter] = details.get(counter)
    if any(
        value is not None and (type(value) is not int or value < 0) for value in counters.values()
    ):
        raise MalformedModelResponseError("OpenAI token usage must contain nonnegative integers.")
    input_tokens, output_tokens, total = (
        counters[key] for key in ("input_tokens", "output_tokens", "total_tokens")
    )
    if (
        all(value is not None for value in (input_tokens, output_tokens, total))
        and input_tokens + output_tokens != total
    ) or any(
        component is not None and parent is not None and component > parent
        for component, parent in (
            (counters["cached_tokens"], input_tokens),
            (counters["reasoning_tokens"], output_tokens),
            (input_tokens, total),
            (output_tokens, total),
        )
    ):
        raise MalformedModelResponseError("OpenAI token usage contains inconsistent counts.")
    return counters
