use super::files;
use crate::backend::{BackendError, Config, Result};
use std::{
    cell::RefCell,
    collections::HashMap,
    fs::{File, OpenOptions},
    marker::PhantomData,
    os::{
        fd::{AsFd, BorrowedFd},
        unix::fs::OpenOptionsExt,
    },
    path::PathBuf,
    rc::Rc,
    sync::{Mutex, OnceLock},
};

static OWNERS: OnceLock<Mutex<HashMap<PathBuf, std::thread::ThreadId>>> = OnceLock::new();
thread_local! { static LEASES: RefCell<HashMap<PathBuf, Rc<File>>> = RefCell::new(HashMap::new()); }
const BUSY: &str = "다른 로컬 작업이 진행 중입니다. 완료 후 다시 시도해 주세요.";
pub(crate) const OPERATION_BUSY: &str = "operation_busy";

pub struct OperationGuard {
    path: PathBuf,
    file: Rc<File>,
    _thread: PhantomData<Rc<()>>,
}
impl AsFd for OperationGuard {
    fn as_fd(&self) -> BorrowedFd<'_> {
        self.file.as_fd()
    }
}
impl OperationGuard {
    pub fn borrowed_lease(&self) -> BorrowedFd<'_> {
        self.as_fd()
    }
}
impl Drop for OperationGuard {
    fn drop(&mut self) {
        if Rc::strong_count(&self.file) == 2 {
            LEASES.with(|held| {
                held.borrow_mut().remove(&self.path);
            });
            if let Ok(mut owners) = OWNERS.get_or_init(Default::default).lock() {
                owners.remove(&self.path);
            }
        }
    }
}

pub fn operation_lock(config: &Config, _purpose: &str) -> Result<OperationGuard> {
    let path = files::resolve(&config.data_dir)?;
    if let Some(file) = LEASES.with(|held| held.borrow().get(&path).cloned()) {
        return Ok(OperationGuard {
            path,
            file,
            _thread: PhantomData,
        });
    }
    {
        let mut owners = OWNERS
            .get_or_init(Default::default)
            .lock()
            .map_err(|_| BackendError::unavailable("로컬 작업 상태를 확인하지 못했습니다."))?;
        if owners.contains_key(&path) {
            return Err(BackendError::new(409, OPERATION_BUSY, BUSY));
        }
        owners.insert(path.clone(), std::thread::current().id());
    }
    let acquired = (|| {
        files::private_directory(&config.data_dir, config)?;
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .mode(0o600)
            .custom_flags(libc::O_NOFOLLOW)
            .open(path.join("operations.lock"))?;
        files::lock(&file, libc::LOCK_EX | libc::LOCK_NB).map_err(|error| {
            if error.kind() == std::io::ErrorKind::WouldBlock {
                BackendError::new(
                    409,
                    OPERATION_BUSY,
                    "다른 창이나 서버에서 로컬 작업을 진행 중입니다.",
                )
            } else {
                error.into()
            }
        })?;
        Ok::<_, BackendError>(Rc::new(file))
    })();
    match acquired {
        Ok(file) => {
            LEASES.with(|held| held.borrow_mut().insert(path.clone(), file.clone()));
            Ok(OperationGuard {
                path,
                file,
                _thread: PhantomData,
            })
        }
        Err(error) => {
            if let Ok(mut owners) = OWNERS.get_or_init(Default::default).lock() {
                owners.remove(&path);
            }
            Err(error)
        }
    }
}

pub fn operation_active(config: &Config) -> Result<bool> {
    match operation_lock(config, "probe") {
        Ok(_) => Ok(false),
        Err(error) if error.code == OPERATION_BUSY => Ok(true),
        Err(error) => Err(error),
    }
}
