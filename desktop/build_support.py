"""Build-only helpers for portable Python metadata and private-path checks."""

import gzip
import importlib
import marshal
from pathlib import Path
import pprint
import re
import shlex
import sys
import sysconfig
import types
import zipfile


RUNTIME_PREFIX = "@LOCALBRAIN_RUNTIME_PREFIX@"


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
