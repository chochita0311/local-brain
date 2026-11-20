fn main() {
    println!("cargo:rerun-if-env-changed=LOCALBRAIN_CORE_BUILD");
    let build = std::env::var("LOCALBRAIN_CORE_BUILD").unwrap_or_else(|_| "unbuilt".into());
    println!("cargo:rustc-env=LOCALBRAIN_CORE_BUILD={build}");
}
