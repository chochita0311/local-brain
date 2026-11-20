use crate::backend::{
    rendering::{render_markdown, MarkdownOptions},
    BackendError, Result,
};
use serde_json::{json, Value};
pub fn conversation_event_view(event: &Value) -> Result<Value> {
    if !event.is_object() {
        return Err(BackendError::invalid(
            "conversation",
            "Conversation event must expose keys or attributes",
        ));
    }
    let mut view = event.clone();
    if !matches!(view["role"].as_str(), Some("user" | "assistant")) {
        return Ok(view);
    }
    let Some(text) = view["text"].as_str() else {
        return Ok(view);
    };
    let rendered = render_markdown(text, &MarkdownOptions::default());
    view["rendered_body"] = json!(rendered.html);
    view["render_state"] = json!(rendered.state);
    view["render_properties"] = json!(rendered.properties);
    Ok(view)
}
pub fn conversation_event_views(events: &[Value]) -> Result<Vec<Value>> {
    events.iter().map(conversation_event_view).collect()
}
