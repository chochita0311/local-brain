use crate::{
    routes,
    state::{AppState, FeatureBindings},
};
use axum::{
    extract::{ConnectInfo, Request},
    middleware::{self, Next},
    response::Response,
};
use localbrain_core::backend::{BackendError, Config, Result};
use std::{
    future::IntoFuture,
    io::{Read, Write},
    net::SocketAddr,
    time::{Duration, Instant},
};

pub fn serve(
    config: Config,
    host: &str,
    port: u16,
    desktop_owner: bool,
    access_log: bool,
) -> Result<()> {
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .thread_stack_size(localbrain_core::backend::WORKER_STACK_BYTES)
        .build()?;
    runtime.block_on(async move{
        let token=if config.desktop{std::env::var("LOCALBRAIN_DESKTOP_TOKEN").ok().filter(|token|!token.is_empty()).ok_or_else(||BackendError::unavailable("The backend must be launched by LocalBrain.app"))?}else{String::new()};
        let selected=FeatureBindings::for_config(&config)?;
        let state=tokio::task::spawn_blocking(move||AppState::initialize(config,token,selected)).await.map_err(|_|BackendError::unavailable("LocalBrain startup interrupted"))??;
        let listener=tokio::net::TcpListener::bind((host,port)).await?;let address=listener.local_addr()?;
        let signal=state.shutdown.clone();
        tokio::spawn(async move{
            #[cfg(unix)]
            {
                if let Ok(mut terminate)=tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()){
                    tokio::select!{_=tokio::signal::ctrl_c()=>{},_=terminate.recv()=>{}}
                }else{let _=tokio::signal::ctrl_c().await;}
            }
            #[cfg(not(unix))]
            {let _=tokio::signal::ctrl_c().await;}
            signal.request();
        });
        if desktop_owner{
            let signal=state.shutdown.clone();std::thread::Builder::new().name("desktop-owner".into()).spawn(move||{let mut input=std::io::stdin().lock();let mut bytes=[0;4096];loop{match input.read(&mut bytes){Ok(0)|Err(_)=>break,Ok(_)=>{}}}signal.request();})?;
        }
        let shutdown=state.shutdown.clone();let finish=state.shutdown.clone();
        let mut router=routes::router(state.clone());
        if access_log {
            router = router.layer(middleware::from_fn(log_request));
        }
        let service = router.into_make_service_with_connect_info::<SocketAddr>();
        let server = axum::serve(listener, service)
            .with_graceful_shutdown(async move { shutdown.wait().await; })
            .into_future();
        tokio::pin!(server);
        // Readiness is emitted only after all services, templates and the
        // loopback listener are ready. Desktop stdout is its launch protocol.
        if desktop_owner {
            println!("{}", serde_json::json!({"ready":true,"port":address.port()}));
            std::io::stdout().flush()?;
        } else {
            let log_state = if access_log { "on" } else { "off" };
            let _ = writeln!(
                std::io::stderr().lock(),
                "LocalBrain ready: http://{address} (access log: {log_state})"
            );
        }
        let outcome=tokio::select!{
            result=&mut server=>result.map_err(BackendError::from),
            _=async{finish.wait().await;tokio::time::sleep(Duration::from_secs(30)).await;}=>Err(BackendError::unavailable("LocalBrain shutdown exceeded its grace period")),
        };
        state.shutdown.request();
        let services=state.services.clone();let stopped=tokio::task::spawn_blocking(move||services.stop()).await.map_err(|_|BackendError::unavailable("LocalBrain service shutdown interrupted"))?;
        outcome?;stopped?;Ok(())
    })
}

async fn log_request(request: Request, next: Next) -> Response {
    let method = request.method().clone();
    let uri = request.uri().clone();
    let version = request.version();
    let peer = request
        .extensions()
        .get::<ConnectInfo<SocketAddr>>()
        .copied();
    let started = Instant::now();
    let response = next.run(request).await;
    let elapsed = started.elapsed();
    let peer: &dyn std::fmt::Display = match &peer {
        Some(ConnectInfo(address)) => address,
        None => &"-",
    };
    // Keep the encoded path, omitting query data and escaping for a single log line.
    let path = uri.path().escape_debug();
    // A console I/O error must not change the HTTP response.
    let _ = writeln!(
        std::io::stderr().lock(),
        "INFO:     {peer} - \"{method} {path} {version:?}\" {} {:.3}ms",
        response.status(),
        elapsed.as_secs_f64() * 1000.0
    );
    response
}
