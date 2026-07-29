from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime

MAX_CURSOR_LENGTH = 512


class InvalidCursorError(ValueError):
    """Raised when an opaque headlines cursor cannot be validated."""


@dataclass(frozen=True, slots=True)
class NewsCursor:
    published_at: datetime
    article_id: int


def encode_cursor(cursor: NewsCursor) -> str:
    payload = json.dumps(
        {
            "publishedAt": cursor.published_at.astimezone(UTC).isoformat(),
            "id": cursor.article_id,
        },
        separators=(",", ":"),
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_cursor(value: str) -> NewsCursor:
    if not value or len(value) > MAX_CURSOR_LENGTH:
        raise InvalidCursorError("Invalid headlines cursor")
    try:
        padding = "=" * (-len(value) % 4)
        decoded = base64.b64decode(value + padding, altchars=b"-_", validate=True)
        payload = json.loads(decoded)
        if not isinstance(payload, dict) or set(payload) != {"publishedAt", "id"}:
            raise ValueError
        published_at = datetime.fromisoformat(payload["publishedAt"])
        article_id = payload["id"]
        if published_at.tzinfo is None or type(article_id) is not int or article_id < 1:
            raise ValueError
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidCursorError("Invalid headlines cursor") from error
    return NewsCursor(published_at=published_at.astimezone(UTC), article_id=article_id)
