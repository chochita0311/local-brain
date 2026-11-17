#!/usr/bin/env python3
"""Build the public, offline macOS terminal payload. Never copy a user's runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktop"))
from build_support import rust_build_environment

NODE_VERSION = "24.15.0"
ARCHIVE = "node-v" + NODE_VERSION + "-darwin-arm64.tar.gz"
OWNER = ".localbrain-terminal-build"
OWNER_BYTES = b"localbrain.terminal.public-payload.v1\n"


def run(command, **options):
    return subprocess.run(list(map(str, command)), check=True, **options)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def input_identity():
    paths = [ROOT / "rust/Cargo.toml", ROOT / "rust/Cargo.lock", Path(__file__)]
    for folder in (ROOT / "rust/localbrain-core", ROOT / "rust/localbrain-runtime", ROOT / "src/localbrain/terminal"):
        paths += [p for p in folder.rglob("*") if p.is_file() and not p.is_symlink()
                  and p.suffix in {".rs", ".cjs", ".toml", ".json"} and "__pycache__" not in p.parts]
    value = hashlib.sha256()
    for path in sorted(set(paths)):
        value.update(path.relative_to(ROOT).as_posix().encode() + b"\0" + path.read_bytes())
    return value.hexdigest()


def macho(path):
    with path.open("rb") as stream:
        return stream.read(4) in {b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"}


def finalize(payload, *, provenance=None):
    """Hash the final signed bytes; Tauri may re-sign bundled Mach-O resources."""
    manifest_path = payload / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    files = []
    for path in sorted(payload.rglob("*")):
        if path.is_symlink():
            raise ValueError("Payload symlinks are not allowed: " + path.relative_to(payload).as_posix())
        if not path.is_file() or path == manifest_path:
            continue
        executable = os.access(path, os.X_OK)
        path.chmod(0o700 if executable else 0o600)
        files.append({"path": path.relative_to(payload).as_posix(), "sha256": digest(path),
                      "size": path.stat().st_size, "mode": "0700" if executable else "0600"})
    value = {"schema": 1, "target": "aarch64-apple-darwin", "minimumOs": "14.0",
             "managerProtocol": 2, "hostProtocol": 1, "helperProtocol": 1,
             "checkpointVersion": "xterm6-v3", "unicodeVersion": "11",
             "node": {"version": NODE_VERSION, "abi": 137, "napi": 10, "platform": "darwin", "arch": "arm64"},
             "core": {"version": "0.1.0", "rustVersion": previous["core"]["rustVersion"] if previous else subprocess.check_output(["rustc", "--version"], text=True).strip()},
             "engine": {"nodePty": "1.1.0", "headless": "6.0.0", "serialize": "0.14.0", "unicode11": "0.9.0"},
             "runtimeLockSha256": digest(payload / "engine/package-lock.json"),
             "provenance": provenance or previous["provenance"], "files": files}
    value["payloadId"] = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    manifest_path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    manifest_path.chmod(0o600)
    return value


def download(url, path):
    with urllib.request.urlopen(url, timeout=90) as response, path.open("xb") as output:
        shutil.copyfileobj(response, output)


def output_path(destination):
    destination = destination.expanduser().absolute()
    if destination.is_symlink():
        raise ValueError("Refusing to replace a linked terminal build")
    destination = destination.resolve()
    if destination.exists():
        marker = destination / OWNER
        try:
            info = marker.lstat()
            owned = (destination.is_dir() and destination.stat().st_uid == os.getuid()
                     and stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                     and info.st_nlink == 1 and info.st_size == len(OWNER_BYTES)
                     and marker.read_bytes() == OWNER_BYTES)
        except OSError:
            owned = False
        if not owned:
            raise ValueError("Refusing to replace an unowned terminal build")
    return destination


def cargo_artifact(output):
    artifacts = []
    for line in output.splitlines():
        message = json.loads(line)
        target = message.get("target", {})
        if message.get("reason") == "compiler-artifact" and target.get("name") == "localbrain-runtime" and "bin" in target.get("kind", []):
            executable = message.get("executable")
            if not isinstance(executable, str) or not Path(executable).is_absolute():
                raise ValueError("Cargo did not identify an absolute runtime executable")
            artifacts.append(Path(executable))
    if len(artifacts) != 1 or not artifacts[0].is_file():
        raise ValueError("Expected exactly one built runtime executable")
    return artifacts[0]


def build(destination, archive=None, checksums=None):
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError("Build the aarch64-apple-darwin payload on Apple Silicon macOS")
    destination = output_path(destination)
    before = input_identity()
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".terminal-build-", dir=destination.parent) as temporary:
        work = Path(temporary)
        if archive is None or checksums is None:
            archive, checksums = work / ARCHIVE, work / "SHASUMS256.txt"
            download("https://nodejs.org/dist/v" + NODE_VERSION + "/" + ARCHIVE, archive)
            download("https://nodejs.org/dist/v" + NODE_VERSION + "/SHASUMS256.txt", checksums)
        expected = [line.split()[0] for line in checksums.read_text().splitlines() if line.split()[1:] == [ARCHIVE]]
        if len(expected) != 1 or digest(archive) != expected[0]:
            raise ValueError("Official Node archive SHA256 verification failed")
        payload = work / "runtime"
        for folder in ("bin", "manager", "engine", "licenses"):
            (payload / folder).mkdir(parents=True)
        prefix = ARCHIVE.removesuffix(".tar.gz")
        with tarfile.open(archive, "r:gz") as source:
            for name, target in (("bin/node", "bin/node"), ("LICENSE", "licenses/Node-LICENSE.txt")):
                member = source.getmember(prefix + "/" + name)
                if not member.isfile():
                    raise ValueError("Expected a regular Node release file")
                with source.extractfile(member) as input, (payload / target).open("xb") as output:
                    shutil.copyfileobj(input, output)
        (payload / "bin/node").chmod(0o700)
        env = rust_build_environment(os.environ, (Path.home(), ROOT, work))
        env["MACOSX_DEPLOYMENT_TARGET"] = "14.0"
        compiled = run(["cargo", "build", "--locked", "--release", "--target", "aarch64-apple-darwin", "--message-format=json-render-diagnostics", "--manifest-path", ROOT / "rust/Cargo.toml"], env=env, capture_output=True, text=True)
        executable = cargo_artifact(compiled.stdout)
        if subprocess.check_output(["/usr/bin/lipo", "-archs", str(executable)], text=True).strip() != "arm64":
            raise ValueError("The Rust helper is not the declared arm64 target")
        shutil.copyfile(executable, payload / "bin/localbrain-runtime")
        (payload / "bin/localbrain-runtime").chmod(0o700)
        for path in (ROOT / "src/localbrain/terminal").glob("*.cjs"):
            shutil.copyfile(path, payload / "manager" / path.name)
        for name in ("package.json", "package-lock.json"):
            shutil.copyfile(ROOT / "src/localbrain/terminal/runtime" / name, payload / "engine" / name)
        run(["npm", "ci", "--ignore-scripts", "--omit=dev", "--no-audit", "--no-fund"], cwd=payload / "engine")
        bin_links = payload / "engine/node_modules/.bin"
        if bin_links.exists():
            shutil.rmtree(bin_links)
        # Retain only the deployment architecture's native prebuilds.
        prebuilds = payload / "engine/node_modules/node-pty/prebuilds"
        for folder in prebuilds.iterdir():
            if folder.name != "darwin-arm64":
                shutil.rmtree(folder)
        for path in payload.rglob("*"):
            if path.is_symlink():
                raise ValueError("Unexpected dependency symlink")
            if path.is_file():
                executable = path.name in {"node", "localbrain-runtime", "spawn-helper"}
                path.chmod(0o700 if executable else 0o600)
                if macho(path):
                    run(["codesign", "--force", "--sign", "-", path], capture_output=True)
                    run(["codesign", "--verify", "--strict", path], capture_output=True)
        probe = json.loads(subprocess.check_output([str(payload / "bin/node"), "-p", "JSON.stringify({version:process.versions.node,abi:Number(process.versions.modules),napi:Number(process.versions.napi),platform:process.platform,arch:process.arch})"], text=True))
        if probe != {"version": NODE_VERSION, "abi": 137, "napi": 10, "platform": "darwin", "arch": "arm64"}:
            raise ValueError("Node ABI probe failed")
        # Preserve full public upstream texts without recording registry/build paths.
        metadata = json.loads(subprocess.check_output(["cargo", "metadata", "--locked", "--offline", "--format-version", "1", "--manifest-path", str(ROOT / "rust/Cargo.toml")], text=True))
        notices = []
        for package in sorted(metadata["packages"], key=lambda p: (p["name"], p["version"])):
            if not package["source"]:
                continue
            notices.append("## " + package["name"] + " " + package["version"] + "\n" + (package.get("license") or "See upstream terms"))
            for file in sorted(Path(package["manifest_path"]).parent.iterdir()):
                if file.is_file() and file.name.lower().startswith(("license", "licence", "copying", "notice", "copyright")):
                    notices.append(file.read_text(errors="replace"))
        (payload / "licenses/Rust-THIRD-PARTY-NOTICES.txt").write_text("\n\n".join(notices) + "\n")
        records = json.loads(subprocess.check_output([str(payload / "bin/localbrain-runtime"), "process-snapshot"], timeout=3))
        if not isinstance(records, list) or any(set(record) != {"pid", "parent", "group", "session", "born", "dead"} for record in records):
            raise ValueError("Rust helper protocol probe failed")
        (payload / OWNER).write_bytes(OWNER_BYTES)
        (payload / OWNER).chmod(0o600)
        if input_identity() != before or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != source_commit:
            raise ValueError("Runtime build inputs changed during packaging")
        provenance = {"sourceCommit": source_commit,
                      "inputSha256": before, "nodeArchiveSha256": expected[0], "signing": "ad-hoc"}
        manifest = finalize(payload, provenance=provenance)
        output_path(destination)  # Recheck ownership before publishing.
        # Keep a recovery copy outside TemporaryDirectory's automatic cleanup.
        backup = destination.with_name("." + destination.name + ".previous-" + uuid.uuid4().hex)
        if destination.exists():
            destination.rename(backup)
        try:
            payload.rename(destination)
        except BaseException:
            try:
                if backup.exists() and not destination.exists():
                    backup.rename(destination)
            except BaseException as recovery:
                raise RuntimeError("Runtime publication recovery required; previous output retained at " + str(backup)) from recovery
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "desktop/terminal/runtime")
    parser.add_argument("--node-archive", type=Path)
    parser.add_argument("--node-checksums", type=Path)
    args = parser.parse_args()
    value = build(args.output, args.node_archive, args.node_checksums)
    print(json.dumps({"payloadId": value["payloadId"], "files": len(value["files"])}))
