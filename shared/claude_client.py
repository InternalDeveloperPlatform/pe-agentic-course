"""
shared/claude_client.py
-----------------------
Single entry point for all Claude API calls across the course.
Students do not modify this file — they call ask() from their agent scripts.
"""

import os
import json
import anthropic


def _sanitize_json(raw: str) -> str:
    """
    Replace literal newlines (and other control characters) that appear
    inside JSON string values with their proper escape sequences.

    Claude occasionally writes multi-line strings in JSON without escaping
    the embedded newlines, which makes json.loads() raise JSONDecodeError.
    A simple character-level state machine handles nested quotes and
    backslash escapes correctly.
    """
    result = []
    in_string = False
    escape_next = False
    for ch in raw:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == '\\' and in_string:
            result.append(ch)
            escape_next = True
        elif ch == '"':
            result.append(ch)
            in_string = not in_string
        elif in_string and ch == '\n':
            result.append('\\n')
        elif in_string and ch == '\r':
            result.append('\\r')
        elif in_string and ch == '\t':
            result.append('\\t')
        else:
            result.append(ch)
    return ''.join(result)

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Run: export ANTHROPIC_API_KEY=your_key_here"
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def ask(
    system: str,
    user: str,
    model: str = "claude-opus-4-5-20251101",
    max_tokens: int = 1024,
) -> dict:
    """
    Call Claude and return a parsed JSON dict from the response.

    Parameters
    ----------
    system : str
        The system prompt (defines agent role and output schema).
    user : str
        The user message (the context / question for this call).
    model : str
        Claude model string. Defaults to claude-opus-4-5-20251101.
    max_tokens : int
        Maximum tokens for the response.

    Returns
    -------
    dict
        Parsed JSON response from Claude.

    Raises
    ------
    ValueError
        If the response cannot be parsed as JSON.
    anthropic.APIError
        On API-level errors (rate limits, auth, etc.).
    """
    client = _get_client()

    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        raw = message.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        # Repair literal newlines inside JSON string values
        raw = _sanitize_json(raw)

        return json.loads(raw)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude response could not be parsed as JSON.\n"
            f"Raw response:\n{raw}\n\nError: {e}"
        ) from e
