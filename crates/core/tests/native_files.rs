use localbrain_core::backend::storage::files::resolve;
use std::{fs, os::unix::fs::symlink};

#[test]
fn existing_paths_resolve_symlinks_before_parent_components() {
    let root = tempfile::tempdir().unwrap();
    let canonical_root = fs::canonicalize(root.path()).unwrap();
    fs::create_dir_all(root.path().join("actual/inner")).unwrap();
    fs::create_dir(root.path().join("actual/neighbor")).unwrap();
    fs::write(root.path().join("actual/file"), b"synthetic").unwrap();
    symlink("actual/inner", root.path().join("alias")).unwrap();

    assert_eq!(
        resolve(&root.path().join("actual/file")).unwrap(),
        canonical_root.join("actual/file")
    );
    assert_eq!(
        resolve(&root.path().join("alias/../neighbor")).unwrap(),
        canonical_root.join("actual/neighbor")
    );
}

#[test]
fn absent_parent_component_keeps_existing_fallback_semantics() {
    let root = tempfile::tempdir().unwrap();
    let canonical_root = fs::canonicalize(root.path()).unwrap();
    fs::create_dir(root.path().join("existing")).unwrap();
    let path = root.path().join("missing/../existing");

    assert!(fs::canonicalize(&path).is_err());
    assert_eq!(resolve(&path).unwrap(), canonical_root.join("existing"));
    assert!(!root.path().join("missing").exists());
}

#[test]
fn absent_suffix_follows_existing_symlink_without_creating_directories() {
    let root = tempfile::tempdir().unwrap();
    let canonical_root = fs::canonicalize(root.path()).unwrap();
    fs::create_dir(root.path().join("actual")).unwrap();
    symlink("actual", root.path().join("alias")).unwrap();

    assert_eq!(
        resolve(&root.path().join("alias/missing/child")).unwrap(),
        canonical_root.join("actual/missing/child")
    );
    assert!(!root.path().join("actual/missing").exists());
}

#[test]
fn regular_file_with_dot_keeps_existing_resolved_file() {
    let root = tempfile::tempdir().unwrap();
    let file = root.path().join("file");
    fs::write(&file, b"synthetic").unwrap();
    let path = file.join(".");

    assert_eq!(resolve(&path).unwrap(), fs::canonicalize(file).unwrap());
}

#[test]
fn dangling_symlink_keeps_unresolved_fallback_path() {
    let root = tempfile::tempdir().unwrap();
    let canonical_root = fs::canonicalize(root.path()).unwrap();
    symlink("missing-target", root.path().join("dangling")).unwrap();

    assert_eq!(
        resolve(&root.path().join("dangling/child")).unwrap(),
        canonical_root.join("dangling/child")
    );
}

#[test]
fn symlink_loop_remains_an_io_error() {
    let root = tempfile::tempdir().unwrap();
    symlink("second", root.path().join("first")).unwrap();
    symlink("first", root.path().join("second")).unwrap();

    let error = resolve(&root.path().join("first/child")).unwrap_err();
    assert_eq!(error.code, "io");
    assert_eq!(
        error.message,
        std::io::Error::from_raw_os_error(libc::ELOOP).to_string()
    );
}
