use std::{
    io::{BufRead, BufReader, Read, Write},
    net::TcpStream,
    process::{Child, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        Mutex,
    },
    thread,
    time::{Duration, Instant},
};
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_opener::OpenerExt;

#[derive(Default)]
struct Backend {
    child: Mutex<Option<Child>>,
    port: Mutex<Option<u16>>,
    token: Mutex<String>,
    quitting: AtomicBool,
    starting: AtomicBool,
}

fn show(app: &tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
    }
}

fn failure(app: &tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.navigate("tauri://localhost/index.html".parse().unwrap());
        let handle = app.clone();
        thread::spawn(move || {
            thread::sleep(Duration::from_millis(500));
            if let Some(window) = handle.get_webview_window("main") {
                let _ = window.eval("document.getElementById('status').textContent='시작하지 못했거나 연결이 종료되었습니다. 다른 LocalBrain 실행과 저장공간을 확인한 뒤 다시 시도해 주세요.'; document.getElementById('retry').hidden=false;");
            }
        });
    }
}

fn start_backend(app: tauri::AppHandle) -> Result<(), String> {
    let state = app.state::<Backend>();
    if state.starting.swap(true, Ordering::SeqCst) {
        return Ok(());
    }
    {
        let mut slot = state.child.lock().unwrap();
        if let Some(child) = slot.as_mut() {
            if child.try_wait().map_err(|e| e.to_string())?.is_none() {
                state.starting.store(false, Ordering::SeqCst);
                return Ok(());
            }
        }
    }
    let path = match app.path().resource_dir() {
        Ok(path) => path.join("backend/localbrain-backend"),
        Err(_) => {
            state.starting.store(false, Ordering::SeqCst);
            failure(&app);
            return Err("앱 리소스 위치를 찾지 못했습니다.".into());
        }
    };
    let token = uuid::Uuid::new_v4().to_string();
    let child = Command::new(path)
        .env("LOCALBRAIN_DESKTOP_TOKEN", &token)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn();
    let mut child = match child {
        Ok(child) => child,
        Err(_) => {
            state.starting.store(false, Ordering::SeqCst);
            failure(&app);
            return Err("앱의 실행 파일을 시작하지 못했습니다.".into());
        }
    };
    let stdout = child.stdout.take().unwrap();
    let child_id = child.id();
    *state.child.lock().unwrap() = Some(child);
    *state.token.lock().unwrap() = token.clone();
    *state.port.lock().unwrap() = None;
    let watchdog = app.clone();
    thread::spawn(move || {
        let deadline = Instant::now() + Duration::from_secs(90);
        while Instant::now() < deadline {
            let state = watchdog.state::<Backend>();
            if state.quitting.load(Ordering::SeqCst) || state.port.lock().unwrap().is_some() {
                return;
            }
            if state.child.lock().unwrap().as_ref().map(Child::id) != Some(child_id) {
                return;
            }
            thread::sleep(Duration::from_millis(250));
        }
        let state = watchdog.state::<Backend>();
        let mut slot = state.child.lock().unwrap();
        if state.port.lock().unwrap().is_none() {
            if let Some(child) = slot.as_mut().filter(|child| child.id() == child_id) {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    });
    thread::spawn(move || {
        for line in BufReader::new(stdout).lines().map_while(Result::ok) {
            if let Ok(value) = serde_json::from_str::<serde_json::Value>(&line) {
                if value["ready"] == true {
                    if let Some(port) = value["port"].as_u64().filter(|p| *p > 0 && *p <= 65535) {
                        *app.state::<Backend>().port.lock().unwrap() = Some(port as u16);
                        if let Some(window) = app.get_webview_window("main") {
                            let url =
                                format!("http://127.0.0.1:{}/desktop/start?token={}", port, token);
                            let _ = window.navigate(url.parse().unwrap());
                        }
                        app.state::<Backend>()
                            .starting
                            .store(false, Ordering::SeqCst);
                    }
                }
            }
        }
        let state = app.state::<Backend>();
        if state.child.lock().unwrap().as_ref().map(Child::id) == Some(child_id) {
            state.starting.store(false, Ordering::SeqCst);
            if !state.quitting.load(Ordering::SeqCst) {
                failure(&app);
            }
        }
    });
    Ok(())
}

fn stop_backend(app: &tauri::AppHandle) {
    let state = app.state::<Backend>();
    let port = *state.port.lock().unwrap();
    if let Some(port) = port {
        if let Ok(mut stream) = TcpStream::connect_timeout(
            &format!("127.0.0.1:{port}").parse().unwrap(),
            Duration::from_secs(2),
        ) {
            let _ = stream.set_read_timeout(Some(Duration::from_secs(2)));
            let token = state.token.lock().unwrap();
            let _ = write!(stream, "POST /desktop/shutdown HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nAuthorization: Bearer {token}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");
            let mut buffer = [0; 256];
            let _ = stream.read(&mut buffer);
        }
    }
    if let Some(mut child) = state.child.lock().unwrap().take() {
        drop(child.stdin.take());
        let deadline = Instant::now() + Duration::from_secs(40);
        loop {
            match child.try_wait() {
                Ok(Some(_)) | Err(_) => break,
                _ => {}
            }
            if Instant::now() >= deadline {
                let _ = child.kill();
                let _ = child.wait();
                break;
            }
            thread::sleep(Duration::from_millis(100));
        }
    };
}

#[tauri::command]
fn retry_backend(app: tauri::AppHandle) -> Result<(), String> {
    start_backend(app)
}

#[tauri::command]
async fn choose_path(app: tauri::AppHandle, directory: bool) -> Result<Option<String>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let dialog = app.dialog().file();
        let selected = if directory {
            dialog.blocking_pick_folder()
        } else {
            dialog.blocking_pick_file()
        };
        selected
            .map(|p| {
                p.into_path()
                    .map(|p| p.to_string_lossy().to_string())
                    .map_err(|e| e.to_string())
            })
            .transpose()
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
fn open_external(app: tauri::AppHandle, url: String) -> Result<(), String> {
    let parsed: tauri::Url = url.parse().map_err(|_| "잘못된 링크입니다.".to_string())?;
    if !["http", "https"].contains(&parsed.scheme()) || parsed.host_str().is_none() {
        return Err("웹 링크만 외부 브라우저에서 열 수 있습니다.".into());
    }
    app.opener()
        .open_url(url, None::<&str>)
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn choose_backup_path(app: tauri::AppHandle) -> Result<Option<String>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        app.dialog()
            .file()
            .set_file_name("LocalBrain-backup.zip")
            .add_filter("ZIP backup", &["zip"])
            .blocking_save_file()
            .map(|p| {
                p.into_path()
                    .map(|p| p.to_string_lossy().to_string())
                    .map_err(|e| e.to_string())
            })
            .transpose()
    })
    .await
    .map_err(|e| e.to_string())?
}

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _, _| show(app)))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .manage(Backend::default())
        .invoke_handler(tauri::generate_handler![
            retry_backend,
            choose_path,
            open_external,
            choose_backup_path
        ])
        .setup(|app| {
            let handle = app.handle().clone();
            let navigation = handle.clone();
            WebviewWindowBuilder::new(app, "main", WebviewUrl::App("index.html".into()))
                .title("LocalBrain")
                .inner_size(1280.0, 850.0)
                .min_inner_size(640.0, 480.0)
                .on_navigation(move |url| {
                    if url.scheme() == "tauri" {
                        return true;
                    }
                    if url.scheme() == "http" && url.host_str() == Some("127.0.0.1") {
                        return url.port() == *navigation.state::<Backend>().port.lock().unwrap();
                    }
                    false
                })
                .build()?;
            use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
            let settings = MenuItem::with_id(app, "settings", "설정…", true, Some("CmdOrCtrl+,"))?;
            let application = Submenu::with_items(
                app,
                "LocalBrain",
                true,
                &[
                    &settings,
                    &PredefinedMenuItem::separator(app)?,
                    &PredefinedMenuItem::hide(app, None)?,
                    &PredefinedMenuItem::separator(app)?,
                    &PredefinedMenuItem::quit(app, None)?,
                ],
            )?;
            let edit = Submenu::with_items(
                app,
                "편집",
                true,
                &[
                    &PredefinedMenuItem::undo(app, None)?,
                    &PredefinedMenuItem::redo(app, None)?,
                    &PredefinedMenuItem::cut(app, None)?,
                    &PredefinedMenuItem::copy(app, None)?,
                    &PredefinedMenuItem::paste(app, None)?,
                    &PredefinedMenuItem::select_all(app, None)?,
                ],
            )?;
            let window_menu = Submenu::with_items(
                app,
                "창",
                true,
                &[
                    &PredefinedMenuItem::minimize(app, None)?,
                    &PredefinedMenuItem::close_window(app, None)?,
                ],
            )?;
            app.set_menu(Menu::with_items(app, &[&application, &edit, &window_menu])?)?;
            app.on_menu_event(|app, event| {
                if event.id().as_ref() == "settings" {
                    show(app);
                    if let Some(window) = app.get_webview_window("main") {
                        let _ =
                            window.eval("window.dispatchEvent(new Event('localbrain-settings'))");
                    }
                }
            });
            thread::spawn(move || {
                let _ = start_backend(handle);
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .build(tauri::generate_context!())
        .expect("LocalBrain could not start");
    app.run(|app, event| match event {
        tauri::RunEvent::ExitRequested { api, code, .. } => {
            if code.is_none() && !app.state::<Backend>().quitting.swap(true, Ordering::SeqCst) {
                api.prevent_exit();
                let handle = app.clone();
                thread::spawn(move || {
                    stop_backend(&handle);
                    handle.exit(0);
                });
            }
        }
        tauri::RunEvent::Exit => stop_backend(app),
        tauri::RunEvent::Reopen { .. } => show(app),
        _ => {}
    });
}
