"""Build-only native artifact ownership, input identity, and path inspection."""
import gzip
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import tempfile
import zipfile

BUILD_OUTPUT_MARKER = '.localbrain-build-output'


def owned_build_directory(path):
    marker = path / BUILD_OUTPUT_MARKER
    return path.is_dir() and not path.is_symlink() and marker.is_file() and not marker.is_symlink()


def publish_build(staging, output):
    """Publish a verified app/archive/checksum, restoring prior files on failure."""
    names = ('LocalBrain-apple-silicon', 'LocalBrain-apple-silicon.zip', 'LocalBrain-apple-silicon.sha256')
    previous = output / names[0]
    if previous.is_symlink() or (previous.exists() and not owned_build_directory(previous)):
        raise ValueError('Refusing to replace an unowned build directory')
    for name in names[1:]:
        target = output / name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError('Refusing to replace a non-file build output')
    if not owned_build_directory(staging / names[0]):
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



def runtime_inputs(root):
    """The complete local Cargo dependency source graph, excluding build caches."""
    root = Path(root)
    paths = {root / 'Cargo.toml', root / 'Cargo.lock'}
    for package in (*sorted((root / 'crates').iterdir()), root / 'apps/api'):
        if not package.is_dir() or not (package / 'Cargo.toml').is_file():
            continue
        paths.add(package / 'Cargo.toml')
        if (package / 'build.rs').is_file():
            paths.add(package / 'build.rs')
        for folder in ('src', 'resources'):
            paths.update(path for path in (package / folder).rglob('*')
                         if path.is_file() and not path.is_symlink()
                         and '__pycache__' not in path.parts and path.suffix != '.pyc')
    engine = root / 'crates/runtime/engine'
    paths.update(engine.glob('*.cjs'))
    paths.update(engine / name for name in ('package.json', 'package-lock.json'))
    return paths


def source_identity(root):
    """Fingerprint explicit public build inputs, never private runtime roots."""
    root = Path(root)
    paths = runtime_inputs(root)
    for directory in ('apps/web', 'apps/desktop/src-tauri/src', 'apps/desktop/src-tauri/icons', 'apps/desktop/ui'):
        paths.update(path for path in (root / directory).rglob('*')
                     if path.is_file() and not path.is_symlink()
                     and '__pycache__' not in path.parts and path.suffix != '.pyc'
                     and path != root / 'apps/desktop/ui/app-styles.css')
    paths.update(root / name for name in (
        'apps/desktop/build_support.py', 'apps/desktop/package.json', 'apps/desktop/package-lock.json',
        'apps/desktop/src-tauri/Cargo.toml', 'apps/desktop/src-tauri/Cargo.lock',
        'apps/desktop/src-tauri/build.rs', 'apps/desktop/src-tauri/tauri.conf.json',
        'apps/desktop/src-tauri/Info.plist', 'scripts/build-api.py', 'scripts/build-desktop.py',
        'scripts/build-terminal-runtime.py', 'docs/policies/project/standalone-test-app-guide.md',
    ))
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
    """Keep flags/private paths and reuse Cargo's cache across owned stages.

    Callers supply home, checkout, then staging roots. Standard temporary roots
    have stable aliases so a new staging nonce does not invalidate every crate.
    """
    result = dict(environment)
    encoded = result.get('CARGO_ENCODED_RUSTFLAGS')
    flags = encoded.split('\x1f') if encoded else shlex.split(result.get('RUSTFLAGS', ''))
    roots = [Path(root) for root in private_roots]
    for path in roots:
        if not path.is_absolute() or path == Path('/'):
            raise ValueError('Rust remapping requires absolute non-root build paths')
    if len(roots) < 2:
        raise ValueError('Rust remapping requires the home and checkout roots')
    temporary = sorted({Path('/tmp'), Path('/private/tmp'),
                        Path(tempfile.gettempdir()), Path(tempfile.gettempdir()).resolve()})
    mappings = {path: 'temporary' for path in temporary}
    mappings.update(((roots[0], 'home'), (roots[1], 'source')))
    for index, path in enumerate(roots[2:]):
        if not any(path == parent or parent in path.parents for parent in mappings):
            mappings[path] = f'staging/{index}'
    # rustc uses the last matching prefix; preserve the most specific owner.
    for path, alias in sorted(mappings.items(), key=lambda item: (len(item[0].parts), str(item[0]))):
        flags.append(f'--remap-path-prefix={path}=/localbrain-build/{alias}')
    # Cargo's encoded form preserves paths/flags containing spaces exactly.
    result['CARGO_ENCODED_RUSTFLAGS'] = '\x1f'.join(flags)
    result.pop('RUSTFLAGS', None)
    return result



def stream_contains_paths(stream, private_roots):
    needles = tuple(os.fsencode(str(path)) for path in private_roots)
    overlap = max(map(len, needles), default=1) - 1
    tail = b''
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            return False
        combined = tail + chunk
        if any(needle in combined for needle in needles):
            return True
        tail = combined[-overlap:] if overlap else b''


def check_bundle_paths(root, executable, private_roots):
    """Inspect final native bytes, assets and compressed resources before ZIP."""
    root = Path(root)
    def inspect_name(name):
        parts = PurePosixPath(str(name).replace('\\', '/')).parts
        for component in parts:
            component = component.lower()
            if (PurePosixPath(component).suffix in {'.py', '.pyc', '.pyo', '.pyd', '.pyz'}
                    or component in {'python.framework', '__pycache__', 'base_library.zip'}
                    or component.startswith(('libpython', 'pyinstaller'))
                    or re.match(r'^pythonw?(?:\d+(?:\.\d+)*)?(?:$|[._-])', component)):
                raise ValueError('Python runtime content in native bundle')
        if any(str(private) in str(name) for private in private_roots):
            raise ValueError('Private build path in bundled name')

    def inspect_stream(stream, name):
        inspect_name(name)
        found = stream_contains_paths(stream, private_roots)
        stream.seek(0)
        suffix = PurePosixPath(str(name)).suffix.lower()
        if suffix == '.zip':
            with zipfile.ZipFile(stream) as archive:
                for member in archive.infolist():
                    inspect_name(member.filename)
                    if not member.is_dir():
                        with archive.open(member) as content:
                            found |= inspect_stream(content, member.filename)
        elif suffix == '.gz':
            with gzip.GzipFile(fileobj=stream) as content:
                found |= stream_contains_paths(content, private_roots)
        return found

    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        inspect_name(relative.as_posix())
        if path.is_symlink():
            target = path.readlink()
            inspect_name(target.as_posix())
            try:
                path.resolve(strict=True).relative_to(root.resolve())
            except (OSError, ValueError) as error:
                raise ValueError('Unresolved or external link in native bundle: ' + str(relative)) from error
            continue
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            found = inspect_stream(stream, relative.as_posix())
        if found:
            raise ValueError('Private build path in bundled file: ' + str(path.relative_to(root)))
    description = subprocess.check_output(['/usr/bin/file', '-b', str(executable)], text=True)
    if 'Mach-O' not in description or 'arm64' not in description:
        raise ValueError('Expected a native arm64 backend executable')
    libraries = '\n'.join(subprocess.check_output(['/usr/bin/otool', '-L', str(executable)], text=True).splitlines()[1:]).lower()
    if 'python' in libraries:
        raise ValueError('Native backend links a Python runtime')
