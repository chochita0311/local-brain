#!/usr/bin/env python3
"""Build a native, ad-hoc signed Apple Silicon app without user runtime data."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / 'apps/desktop'
sys.path.insert(0, str(DESKTOP))
from build_support import BUILD_OUTPUT_MARKER as MARKER, check_bundle_paths, rust_build_environment, source_identity, publish_build, owned_build_directory


def run(command, **kwargs):
    subprocess.run(list(map(str, command)), check=True, **kwargs)


def owned_remove(path):
    if not path.exists() and not path.is_symlink():
        return
    if not owned_build_directory(path):
        raise SystemExit('Refusing to replace an unowned build directory: ' + str(path))
    shutil.rmtree(path)



def builder(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / ('scripts/' + name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--node-archive', type=Path, help='Previously downloaded official pinned Node release')
    parser.add_argument('--node-checksums', type=Path, help='Official release SHASUMS256.txt')
    args = parser.parse_args()
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise SystemExit('Build on Apple Silicon macOS.')
    identity = source_identity(ROOT)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    backend = DESKTOP / 'backend'
    cli = DESKTOP / 'node_modules/.bin/tauri'
    if not cli.is_file():
        raise SystemExit('Run npm ci --prefix apps/desktop first.')
    api_builder = builder('build-api')
    runtime_builder = builder('build-terminal-runtime')
    runtime_builder.build(DESKTOP / 'terminal/runtime', args.node_archive, args.node_checksums)
    api_builder.build(backend, desktop=True)
    generated_style = DESKTOP / 'ui/app-styles.css'
    shutil.copyfile(ROOT / 'apps/web/static/styles.css', generated_style)
    try:
        with tempfile.TemporaryDirectory(prefix='localbrain-app-build-') as directory, \
                tempfile.TemporaryDirectory(prefix='.localbrain-build-', dir=output) as staging_directory:
            work = Path(directory)
            staging = Path(staging_directory)
            build_env = {key: value for key, value in os.environ.items() if key not in {
                'APPLE_ID', 'APPLE_PASSWORD', 'APPLE_TEAM_ID', 'APPLE_API_KEY', 'APPLE_API_ISSUER', 'APPLE_API_KEY_PATH'}}
            build_env = rust_build_environment(build_env, (Path.home(), ROOT, work))
            build_env['MACOSX_DEPLOYMENT_TARGET'] = '14.0'
            run([cli, 'build', '--target', 'aarch64-apple-darwin', '--bundles', 'app'], cwd=DESKTOP, env=build_env)
            built = DESKTOP / 'src-tauri/target/aarch64-apple-darwin/release/bundle/macos/LocalBrain.app'
            runtime_receipt = runtime_builder.finalize(built / 'Contents/Resources/terminal/runtime')
            backend_receipt = api_builder.finalize(built / 'Contents/Resources/backend')
            run(['codesign', '--force', '--sign', '-', built])
            run(['codesign', '--verify', '--deep', '--strict', built])
            deliverable = staging / 'LocalBrain-apple-silicon'
            deliverable.mkdir()
            (deliverable / MARKER).write_text('localbrain standalone test distribution\n')
            app = deliverable / 'LocalBrain.app'
            run(['ditto', built, app])
            shutil.copyfile(ROOT / 'docs/policies/project/standalone-test-app-guide.md', deliverable / 'READ-ME.md')
            api_builder.third_party_notices(deliverable / 'THIRD-PARTY-NOTICES.txt',
                                            [ROOT / 'Cargo.toml', DESKTOP / 'src-tauri/Cargo.toml'])
            size = sum(path.stat().st_size for path in app.rglob('*') if path.is_file() and not path.is_symlink())
            version = plistlib.loads((app / 'Contents/Info.plist').read_bytes())['CFBundleShortVersionString']
            final_identity = source_identity(ROOT)
            if any(final_identity[key] != identity[key] for key in ('commit', 'input_sha256')):
                raise SystemExit('Build inputs changed during packaging; rebuild the current source.')
            (deliverable / 'BUILD-INFO.md').write_text(
                '# LocalBrain test build\n\n' +
                '- Version: ' + version + '\n' +
                '- Source commit: ' + identity['commit'] + '\n' +
                '- Source dirty: ' + str(identity['dirty']).lower() + '\n' +
                '- Build-input SHA256: ' + identity['input_sha256'] + '\n' +
                '- Build-input files: ' + str(identity['input_files']) + '\n' +
                '- Backend: Rust; Python runtime: absent\n' +
                '- Backend executable SHA256: ' + backend_receipt['executables']['localbrain-backend'] + '\n' +
                '- Terminal payload: ' + runtime_receipt['payloadId'] + '\n' +
                '- Rust: ' + backend_receipt['rust'] + '\n' +
                '- Built: ' + datetime.now(timezone.utc).isoformat() + '\n' +
                '- Build OS: macOS ' + platform.mac_ver()[0] + '\n' +
                '- Architecture: arm64; declared minimum macOS: 14\n' +
                '- App bytes (regular files): ' + str(size) + '\n' +
                '- Signing: ad-hoc; notarization: not requested\n' +
                '- Builder checks: native build, deep codesign verification, Python runtime absence and private build-path inspection\n' +
                '- Runtime/browser verification: record separately before distribution\n')
            check_bundle_paths(deliverable, app / 'Contents/Resources/backend/localbrain-backend', (Path.home(), ROOT, work))
            archive = staging / 'LocalBrain-apple-silicon.zip'
            run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', deliverable, archive])
            digest = hashlib.sha256()
            with archive.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(chunk)
            (staging / 'LocalBrain-apple-silicon.sha256').write_text(digest.hexdigest() + '  ' + archive.name + '\n')
            publish_build(staging, output)
            print('Created:', output / archive.name)
    finally:
        generated_style.unlink(missing_ok=True)
        owned_remove(backend)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
