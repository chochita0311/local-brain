from typing import Iterable

from .markdown import render_markdown


_MARKDOWN_MESSAGE_ROLES = {"user", "assistant"}


def conversation_event_view(event) -> dict:
    """Copy one presentation event and attach derived Markdown when eligible."""
    if hasattr(event, "keys"):
        view = {key: event[key] for key in event.keys()}
    elif hasattr(event, "__dict__"):
        view = dict(vars(event))
    else:
        raise TypeError("Conversation event must expose keys or attributes")

    text = view.get("text")
    if view.get("role") not in _MARKDOWN_MESSAGE_ROLES or not isinstance(text, str):
        return view

    rendered = render_markdown(text)
    view["rendered_body"] = rendered.html
    view["render_state"] = rendered.state
    view["render_properties"] = rendered.properties
    return view


def conversation_event_views(events: Iterable) -> list:
    return [conversation_event_view(event) for event in events]
