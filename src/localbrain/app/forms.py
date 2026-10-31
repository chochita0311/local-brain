"""Bounded form decoding shared by HTTP adapters."""

from urllib.parse import parse_qs

from fastapi import Request


MAX_FORM_BYTES = 160 * 1024


class FormError(RuntimeError):
    code = "invalid-form"


async def bounded_urlencoded_form(request: Request, *, multiple_fields=()) -> dict:
    content_type = request.headers.get("content-type", "")
    if content_type.split(";", 1)[0].strip().lower() != "application/x-www-form-urlencoded":
        raise FormError("Form encoding is unsupported")
    body = await request.body()
    if len(body) > MAX_FORM_BYTES:
        raise FormError("Form is too large")
    try:
        parsed = parse_qs(
            body.decode("utf-8"), keep_blank_values=True, max_num_fields=128,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise FormError("Form data is invalid") from exc
    return {
        key: values if key in multiple_fields else values[-1]
        for key, values in parsed.items()
        if values
    }
