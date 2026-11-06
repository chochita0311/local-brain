"""Build-only helpers for portable Python metadata and private-path checks."""

import gzip
import hashlib
import importlib
import marshal
import os
from pathlib import Path
import pprint
import re
import shlex
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types
import zipfile


RUNTIME_PREFIX = "@LOCALBRAIN_RUNTIME_PREFIX@"
BUILD_OUTPUT_MARKER = '.localbrain-build-output'


def publish_build(staging, output):
    """Publish a verified app/archive/checksum, restoring prior files on failure."""
    names = ('LocalBrain-apple-silicon', 'LocalBrain-apple-silicon.zip', 'LocalBrain-apple-silicon.sha256')
    previous = output / names[0]
    if previous.is_symlink() or (previous.exists() and not (previous / BUILD_OUTPUT_MARKER).is_file()):
        raise ValueError('Refusing to replace an unowned build directory')
    for name in names[1:]:
        target = output / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError('Refusing to replace a non-file build output')
    if (staging / names[0]).is_symlink() or not (staging / names[0] / BUILD_OUTPUT_MARKER).is_file():
        raise ValueError('A complete owned candidate build is required')
    if any((staging / name).is_symlink() or not (staging / name).is_file() for name in names[1:]):
        raise ValueError('A complete candidate archive and checksum are required')
    backup = Path(tempfile.mkdtemp(prefix='.localbrain-previous-', dir=output))
    try:
        for name in names:
            if (output / name).exists():
                os.replace(output / name, backup / name)
        for name in names:
            os.replace(staging / name, output / name)
    except BaseException:
        try:
            # Reconcile actual paths: interruption can follow a successful rename
            # before Python gets a chance to record that it happened.
            for name in names:
                if not (staging / name).exists() and (output / name).exists():
                    os.replace(output / name, staging / name)
            for name in names:
                if (backup / name).exists():
                    os.replace(backup / name, output / name)
        except BaseException as error:
            raise RuntimeError('Build publication recovery required; previous files retained at ' + str(backup)) from error
        shutil.rmtree(backup)
        raise
    shutil.rmtree(backup)


def source_identity(root):
    """Fingerprint explicit build inputs without inspecting private runtime roots."""
    root = Path(root)
    paths = set()
    for directory in ('src/localbrain', 'desktop/src-tauri/src', 'desktop/src-tauri/icons', 'desktop/ui'):
        paths.update(path for path in (root / directory).rglob('*')
                     if path.is_file() and not path.is_symlink()
                     and '__pycache__' not in path.parts and path.suffix != '.pyc'
                     and path != root / 'desktop/ui/app-styles.css')
    paths.update(root / name for name in (
        'pyproject.toml', 'uv.lock', 'desktop/backend-entry.py', 'desktop/backend.spec', 'desktop/build_support.py',
        'desktop/package.json', 'desktop/package-lock.json', 'desktop/src-tauri/Cargo.toml',
        'desktop/src-tauri/Cargo.lock', 'desktop/src-tauri/build.rs',
        'desktop/src-tauri/tauri.conf.json', 'desktop/src-tauri/Info.plist', 'scripts/build-desktop.py',
        'docs/policies/project/standalone-test-app-guide.md',
    ) if (root / name).is_file())
    digest = hashlib.sha256()
    for path in sorted(paths):
        content = path.read_bytes()
        digest.update(path.relative_to(root).as_posix().encode() + b'\0')
        digest.update(len(content).to_bytes(8, 'big'))
        digest.update(content)
    commit = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    status = subprocess.run(['git', '-C', str(root), 'status', '--porcelain'], capture_output=True, text=True)
    return {'commit': commit.stdout.strip() if commit.returncode == 0 else 'unavailable',
            'dirty': bool(status.stdout) if status.returncode == 0 else None,
            'input_sha256': digest.hexdigest(), 'input_files': len(paths)}


def rust_build_environment(environment, private_roots):
    """Keep user compiler flags while removing builder paths from native code."""
    result = dict(environment)
    encoded = result.get('CARGO_ENCODED_RUSTFLAGS')
    flags = encoded.split('\x1f') if encoded else shlex.split(result.get('RUSTFLAGS', ''))
    for index, root in enumerate(private_roots):
        path = Path(root)
        if not path.is_absolute() or path == Path('/'):
            raise ValueError('Rust remapping requires absolute non-root build paths')
        flags.append(f'--remap-path-prefix={path}=/localbrain-build/{index}')
    # Cargo's encoded form preserves paths/flags containing spaces exactly.
    result['CARGO_ENCODED_RUSTFLAGS'] = '\x1f'.join(flags)
    result.pop('RUSTFLAGS', None)
    return result


def sysconfig_module_source(variables, install_prefixes, private_roots):
    """Keep ABI/build flags, resolving interpreter installation paths at runtime."""
    prefixes = sorted(set(str(path).rstrip("/") for path in install_prefixes), key=len, reverse=True)
    if not prefixes or any(not path or not Path(path).is_absolute() for path in prefixes):
        raise ValueError("Python installation prefixes must be absolute non-root paths")
    values = {}
    for key, value in variables.items():
        if isinstance(value, str):
            for prefix in prefixes:
                value = re.sub(re.escape(prefix) + r"(?=/|$|[\s'\";:])", RUNTIME_PREFIX, value)
            if any(str(root) in value for root in private_roots):
                raise ValueError("Private build path remains in sysconfig field: " + key)
        values[key] = value
    return (
        '"""Python build metadata with installation paths relative to this runtime."""\n'
        "import sys as _sys\n\n"
        "build_time_vars = " + pprint.pformat(values, sort_dicts=True) + "\n"
        "for _key, _value in build_time_vars.items():\n"
        "    if isinstance(_value, str):\n"
        "        build_time_vars[_key] = _value.replace(" + repr(RUNTIME_PREFIX) + ", _sys.prefix)\n"
    )


def write_sysconfig_hook(work_directory):
    """Use a build hook so Analysis caches the sanitized module, never the original."""
    module_name = sysconfig._get_sysconfigdata_name()
    variables = importlib.import_module(module_name).build_time_vars
    root = Path(work_directory) / "portable-sysconfig"
    modules = root / "modules"
    hooks = root / "hooks" / "pre_find_module_path"
    modules.mkdir(parents=True, exist_ok=True)
    hooks.mkdir(parents=True, exist_ok=True)
    source = sysconfig_module_source(
        variables, (sys.base_prefix, sys.base_exec_prefix), (Path.home(),)
    )
    (modules / (module_name + ".py")).write_text(source, encoding="utf-8")
    (hooks / ("hook-" + module_name + ".py")).write_text(
        "def pre_find_module_path(api):\n    api.search_dirs = [" + repr(str(modules)) + "]\n",
        encoding="utf-8",
    )
    return str(hooks.parent)


def code_contains_paths(code, private_roots):
    """Inspect constants and filenames without executing bundled Python code."""
    if isinstance(code, types.CodeType):
        return code_contains_paths(code.co_filename, private_roots) or any(
            code_contains_paths(value, private_roots) for value in code.co_consts
        )
    if isinstance(code, (tuple, frozenset)):
        return any(code_contains_paths(value, private_roots) for value in code)
    if isinstance(code, str):
        return any(str(root) in code for root in private_roots)
    if isinstance(code, bytes):
        return any(str(root).encode() in code for root in private_roots)
    return False


def stream_contains_paths(stream, private_roots):
    needles = [str(root).encode() for root in private_roots]
    overlap = max(map(len, needles), default=1) - 1
    tail = b""
    while chunk := stream.read(1024 * 1024):
        block = tail + chunk
        if any(needle in block for needle in needles):
            return True
        tail = block[-overlap:] if overlap else b""
    return False


def check_bundle_paths(root, executable, private_roots):
    """Fail before ZIP creation if raw files or compressed Python retain build paths."""
    from PyInstaller.archive.readers import CArchiveReader

    root = Path(root)
    private_roots = tuple(private_roots)
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            if code_contains_paths(str(path.readlink()), private_roots):
                raise ValueError("Private build path in link: " + str(path.relative_to(root)))
            continue
        if not path.is_file():
            continue
        with path.open("rb") as stream:
            found = stream_contains_paths(stream, private_roots)
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    data = archive.read(member)
                    found |= code_contains_paths(data, private_roots)
                    if member.endswith(".pyc"):
                        found |= code_contains_paths(marshal.loads(data[16:]), private_roots)
        elif path.suffix == ".gz":
            with gzip.open(path, "rb") as stream:
                found |= stream_contains_paths(stream, private_roots)
        if found:
            raise ValueError("Private build path in bundled file: " + str(path.relative_to(root)))

    archive = CArchiveReader(str(executable))
    for name, entry in archive.toc.items():
        if entry[-1] == "z":
            modules = archive.open_embedded_archive(name)
            for module in modules.toc:
                if code_contains_paths(modules.extract(module), private_roots):
                    raise ValueError("Private build path in bundled Python module: " + module)
        elif entry[-1] in {"s", "m", "M"}:
            if code_contains_paths(marshal.loads(archive.extract(name)), private_roots):
                raise ValueError("Private build path in bundled Python entry: " + name)
