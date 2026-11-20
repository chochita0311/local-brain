use localbrain_core::backend::{db, preferences, sessions, sources, BackendError, Config, Result};
use minijinja::{
    value::{Kwargs, Serde},
    Environment, Value as TemplateValue,
};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs,
    path::Path,
    sync::{Arc, OnceLock},
    time::UNIX_EPOCH,
};
mod metadata;

pub struct Templates {
    environment: Environment<'static>,
    config: Arc<Config>,
}
#[derive(Debug)]
struct RequestUrl {
    origin: String,
    path: String,
    query: String,
}
impl minijinja::value::Object for RequestUrl {
    fn get_value(self: &Arc<Self>, key: &TemplateValue) -> Option<TemplateValue> {
        match key.as_str()? {
            "path" => Some(TemplateValue::from(self.path.clone())),
            "query" => Some(TemplateValue::from(self.query.clone())),
            _ => None,
        }
    }
    fn render(self: &Arc<Self>, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            formatter,
            "{}{}{}{}",
            self.origin,
            self.path,
            if self.query.is_empty() { "" } else { "?" },
            self.query
        )
    }
}
fn template_error(error: impl std::fmt::Display) -> BackendError {
    BackendError::new(500, "template", error.to_string())
}
pub fn value_label(name: &str, value: Value) -> String {
    localbrain_core::backend::value_registry::display_value_label(name, &value)
}
fn trusted_html_paths(template: &str) -> &'static [&'static str] {
    match template {
        "session.html" | "subsession.html" => &["/events/*/rendered_body"],
        "document.html" => &["/document/rendered_body"],
        "context.html" => &["/selected_document/rendered_body"],
        "app-docs.html" => &["/body/html"],
        "dashboard.html" => &[
            "/selected_lessons/*/article_intro",
            "/selected_lessons/*/article_takeaway",
            "/selected_lessons/*/code_preview_html",
            "/selected_lessons/*/article_sections/*/html",
        ],
        "learning-reader.html" | "learning-note.html" => &[
            "/lesson/article_intro",
            "/lesson/article_takeaway",
            "/lesson/code_preview_html",
            "/lesson/article_sections/*/html",
        ],
        "session_insights.html" => &["/report_html"],
        "atlassian-item.html" => &["/metadata_json"],
        _ => &[],
    }
}
fn render_value(value: Value, trusted: &[&str]) -> TemplateValue {
    render_value_at(value, &mut String::new(), trusted)
}
fn render_value_at(value: Value, path: &mut String, trusted: &[&str]) -> TemplateValue {
    match value {
        Value::String(value) if trusted.contains(&path.as_str()) => {
            TemplateValue::from_safe_string(value)
        }
        Value::Array(items) => {
            let length = path.len();
            path.push_str("/*");
            let value = TemplateValue::from_iter(
                items
                    .into_iter()
                    .map(|value| render_value_at(value, path, trusted)),
            );
            path.truncate(length);
            value
        }
        Value::Object(items) => TemplateValue::from_pairs(items.into_iter().map(|(key, value)| {
            let length = path.len();
            path.push('/');
            for ch in key.chars() {
                match ch {
                    '~' => path.push_str("~0"),
                    '/' => path.push_str("~1"),
                    '*' => path.push_str("~2"),
                    _ => path.push(ch),
                }
            }
            let value = render_value_at(value, path, trusted);
            path.truncate(length);
            (key, value)
        })),
        Value::Null => TemplateValue::from(()),
        Value::Bool(value) => TemplateValue::from(value),
        Value::String(value) => TemplateValue::from(value),
        Value::Number(value) => {
            if let Some(value) = value.as_i64() {
                TemplateValue::from(value)
            } else if let Some(value) = value.as_u64() {
                TemplateValue::from(value)
            } else if let Ok(value) = value.as_str().parse::<i128>() {
                TemplateValue::from(value)
            } else if value
                .as_str()
                .strip_prefix('-')
                .unwrap_or(value.as_str())
                .bytes()
                .all(|byte| byte.is_ascii_digit())
            {
                TemplateValue::from(value.to_string())
            } else if let Some(number) = value.as_f64() {
                TemplateValue::from(number)
            } else {
                TemplateValue::from(value.to_string())
            }
        }
    }
}

impl Templates {
    pub fn load(config: Arc<Config>) -> Result<Self> {
        let mut environment = Environment::new();
        minijinja_contrib::add_to_environment(&mut environment);
        environment.set_unknown_method_callback(|state, value, method, args| {
            // Native query projections carry ISO dates as strings. Templates
            // keep their existing date.isoformat() presentation contract.
            if method == "isoformat" && args.is_empty() && value.as_str().is_some() {
                return Ok(value.clone());
            }
            minijinja_contrib::pycompat::unknown_method_callback(state, value, method, args)
        });
        fn load_folder(env: &mut Environment<'static>, root: &Path, folder: &Path) -> Result<()> {
            let mut paths = fs::read_dir(folder)?
                .map(|entry| entry.map(|entry| entry.path()))
                .collect::<std::io::Result<Vec<_>>>()?;
            paths.sort();
            for path in paths {
                if path.is_dir() {
                    load_folder(env, root, &path)?;
                } else if path
                    .extension()
                    .is_some_and(|extension| extension == "html")
                {
                    let name = path
                        .strip_prefix(root)
                        .unwrap()
                        .to_str()
                        .ok_or_else(|| template_error("Template name is not Unicode"))?
                        .replace('\\', "/");
                    env.add_template_owned(name, fs::read_to_string(path)?)
                        .map_err(template_error)?;
                }
            }
            Ok(())
        }
        let root = config.web_root.join("templates");
        load_folder(&mut environment, &root, &root)?;
        let version = fs::read_dir(config.web_root.join("static"))?
            .filter_map(|entry| entry.ok())
            .filter_map(|entry| entry.metadata().ok())
            .filter(|info| info.is_file())
            .filter_map(|info| info.modified().ok()?.duration_since(UNIX_EPOCH).ok())
            .map(|duration| duration.as_nanos())
            .max()
            .ok_or_else(|| template_error("Static assets are missing"))?;
        environment.add_global("asset_version", version.to_string());
        environment.add_global("app_version", "0.0.1");
        environment.add_global("desktop_edition", config.desktop);
        environment.add_global("auto_work_available", !config.desktop);
        for (global, feature) in [
            ("auto_work_package_available", "auto_work"),
            ("workstreams_available", "workstreams"),
            ("atlassian_available", "atlassian"),
            ("context_search_available", "context_search"),
            ("google_drive_available", "google_drive"),
            ("terminal_available", "terminal"),
        ] {
            environment.add_global(global, config.feature(feature));
        }
        environment.add_function("value_label", |name: String, value: TemplateValue| {
            value_label(&name, serde_json::to_value(value).unwrap_or(Value::Null))
        });
        environment.add_function(
            "value_help",
            |name: String| -> std::result::Result<String, minijinja::Error> {
                localbrain_core::backend::value_registry::visible_value_help(&name).map_err(
                    |error| {
                        minijinja::Error::new(minijinja::ErrorKind::InvalidOperation, error.message)
                    },
                )
            },
        );
        let paths = config.clone();
        environment.add_filter("project_path", move |value: TemplateValue| {
            let path = value.as_str().unwrap_or("");
            let label = sessions::home_relative_path(path, &paths);
            if label.is_empty() {
                "미지정".into()
            } else {
                label
            }
        });
        Ok(Self {
            environment,
            config,
        })
    }
    pub fn render(
        &self,
        name: &str,
        origin: &str,
        path: &str,
        query: &str,
        data: Value,
    ) -> Result<String> {
        let mut environment = self.environment.clone();
        if let Some(language) = data["doc_language"].as_str() {
            let language = language.to_owned();
            environment.add_function("guide_href", move |guide: Serde<Value>| {
                format!(
                    "{}?lang={language}",
                    guide.0["href"].as_str().unwrap_or("/help")
                )
            });
        }
        let mut query_params = BTreeMap::new();
        for (key, value) in url::form_urlencoded::parse(query.as_bytes()) {
            query_params.insert(key.into_owned(), value.into_owned());
        }
        let mut values = data
            .as_object()
            .cloned()
            .ok_or_else(|| template_error("Template context must be an object"))?;
        if name == "atlassian-item.html" {
            let metadata = data
                .pointer("/item/metadata")
                .ok_or_else(|| template_error("Item metadata is missing"))?;
            values.insert(
                "metadata_json".into(),
                Value::String(metadata::render(metadata)?),
            );
        }
        let request = TemplateValue::from_pairs([
            (
                "url",
                TemplateValue::from_object(RequestUrl {
                    origin: origin.into(),
                    path: path.into(),
                    query: query.into(),
                }),
            ),
            ("query_params", render_value(json!(query_params), &[])),
        ]);
        let origin = origin.to_owned();
        environment.add_function(
            "url_for",
            move |name: String, kwargs: Kwargs| -> std::result::Result<String, minijinja::Error> {
                let path: String = kwargs.get("path")?;
                kwargs.assert_all_used()?;
                if name != "static" {
                    return Err(minijinja::Error::new(
                        minijinja::ErrorKind::InvalidOperation,
                        "Unknown route name",
                    ));
                }
                Ok(format!("{origin}/static/{}", path.trim_start_matches('/')))
            },
        );
        let config = self.config.clone();
        let profiles = Arc::new(OnceLock::new());
        environment.add_function("source_profile",move|reference:TemplateValue|->std::result::Result<TemplateValue,minijinja::Error>{
            let result: &Result<Value>=profiles.get_or_init(||{let connection=db::connect(&config)?;sources::profiles::profile_map(&connection)});
            let profiles=result.as_ref().map_err(|error|minijinja::Error::new(minijinja::ErrorKind::InvalidOperation,error.to_string()))?;
            let key=reference.as_str().map(ToOwned::to_owned).unwrap_or_else(||reference.to_string());
            Ok(render_value(profiles.get(&key).cloned().unwrap_or_else(||json!({"id":null,"name":"Session","provider_kind":"","color":"gray"})),&[]))
        });
        let config = self.config.clone();
        let preferences = Arc::new(OnceLock::new());
        environment.add_function(
            "local_preferences",
            move || -> std::result::Result<TemplateValue, minijinja::Error> {
                let result: &Result<Value> =
                    preferences.get_or_init(|| preferences::presentation_preferences(&config));
                result
                    .as_ref()
                    .map(|value| render_value(value.clone(), &[]))
                    .map_err(|error| {
                        minijinja::Error::new(
                            minijinja::ErrorKind::InvalidOperation,
                            error.to_string(),
                        )
                    })
            },
        );
        let values = render_value(Value::Object(values), trusted_html_paths(name));
        environment
            .get_template(name)
            .map_err(template_error)?
            .render(minijinja::context! {request,..values})
            .map_err(template_error)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn native_template_values_keep_maps_numbers_sequences_and_escaping() {
        let mut env = Environment::new();
        env.set_auto_escape_callback(|_| minijinja::AutoEscape::Html);
        let data=serde_json::from_str::<Value>(r#"{"item":{"id":7,"amount":0.000000000001,"empty":null,"raw":"<script>x</script>","html":"<strong>safe</strong>"},"items":[{"id":9}]}"#).unwrap();
        let result=env.render_str("{{ item.id }}|{{ item.amount > 0 }}|{{ item.empty is none }}|{{ items[0].id }}|{{ item.raw }}|{{ item.html }}",render_value(data,&["/item/html"])).unwrap();
        assert_eq!(
            result,
            "7|True|True|9|&lt;script&gt;x&lt;&#x2f;script&gt;|<strong>safe</strong>"
        );
    }
    #[test]
    fn metadata_names_cannot_grant_html_trust_outside_the_derived_context_path() {
        let mut env = Environment::new();
        env.set_auto_escape_callback(|_| minijinja::AutoEscape::Html);
        let data = json!({"body":{"html":"<strong>safe</strong>"},"metadata":{"html":"<script>never()</script>"},"body/html":"<script>also-never()</script>"});
        let output=env.render_str("{{ body.html }}|{{ metadata.html }}|{{ self_html }}",render_value(json!({"body":data["body"],"metadata":data["metadata"],"self_html":data["body/html"]}),trusted_html_paths("app-docs.html"))).unwrap();
        assert_eq!(output,"<strong>safe</strong>|&lt;script&gt;never()&lt;&#x2f;script&gt;|&lt;script&gt;also-never()&lt;&#x2f;script&gt;");
    }
    #[test]
    fn request_url_keeps_string_presentation_and_path_query_attributes() {
        let mut env = Environment::new();
        env.set_auto_escape_callback(|_| minijinja::AutoEscape::Html);
        let url = TemplateValue::from_object(RequestUrl {
            origin: "http://127.0.0.1:8123".into(),
            path: "/sessions".into(),
            query: "setup=1&source=1".into(),
        });
        let rendered = env
            .render_str(
                "{{ url }}|{{ url.path }}|{{ url.query }}",
                minijinja::context! {url},
            )
            .unwrap();
        assert_eq!(rendered,"http:&#x2f;&#x2f;127.0.0.1:8123&#x2f;sessions?setup=1&amp;source=1|&#x2f;sessions|setup=1&amp;source=1");
    }
    #[test]
    fn complete_existing_template_bundle_compiles() {
        let root = tempfile::tempdir().unwrap();
        let config = Arc::new(Config::for_data_dir(root.path().join("data")));
        Templates::load(config).unwrap();
    }
}
