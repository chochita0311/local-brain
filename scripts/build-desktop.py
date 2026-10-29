#!/usr/bin/env python3
"""Build a local, ad-hoc signed Apple Silicon test app without user runtime data."""
import argparse
import hashlib
from importlib import metadata
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
MARKER = '.localbrain-build-output'
sys.path.insert(0, str(ROOT / 'desktop'))
from build_support import check_bundle_paths, rust_build_environment


def run(command, **kwargs):
    subprocess.run(command, check=True, **kwargs)


def owned_remove(path):
    if not path.exists():
        return
    if path.is_symlink() or not (path / MARKER).is_file():
        raise SystemExit('Refusing to replace an unowned build directory: ' + str(path))
    shutil.rmtree(path)


def third_party_notices(destination):
    """Carry upstream notices alongside the test app, without build paths."""
    sections = ['LocalBrain bundled dependency notices\n\nPublic model weights are not included.\n']
    python_license = Path(sys.base_prefix) / 'lib' / ('python' + platform.python_version_tuple()[0] + '.' + platform.python_version_tuple()[1]) / 'LICENSE.txt'
    if not python_license.is_file():
        raise SystemExit('The bundled Python license file is missing; preserve its upstream notices before distributing.')
    sections.extend(['\n## Python interpreter ' + platform.python_version() + '\n', python_license.read_text()])
    license_names = ('license', 'licence', 'copying', 'notice', 'copyright')
    for distribution in sorted(metadata.distributions(), key=lambda d: d.metadata.get('Name', '').lower()):
        name = distribution.metadata.get('Name', '')
        if name.lower() == 'localbrain':
            continue
        sections.append('\n## Python: ' + name + ' ' + distribution.version + '\n')
        sections.append(distribution.metadata.get('License-Expression') or distribution.metadata.get('License') or 'See upstream license files.')
        for item in distribution.files or ():
            if Path(item).name.lower().startswith(license_names):
                file = Path(distribution.locate_file(item))
                if file.is_file():
                    sections.append('\n' + file.read_text(errors='replace'))
    packages = json.loads(subprocess.check_output(
        ['cargo', 'metadata', '--locked', '--format-version', '1', '--manifest-path', str(ROOT / 'desktop/src-tauri/Cargo.toml')], text=True))
    for package in sorted(packages['packages'], key=lambda p: (p['name'], p['version'])):
        if not package['source']:
            continue
        sections.append('\n## Rust: ' + package['name'] + ' ' + package['version'] + '\n' + (package.get('license') or 'See upstream license files.'))
        folder = Path(package['manifest_path']).parent
        files = [p for p in folder.iterdir() if p.is_file() and p.name.lower().startswith(license_names)]
        if package.get('license_file'):
            files.append(folder / package['license_file'])
        for file in sorted(set(files)):
            if file.is_file():
                sections.append('\n' + file.read_text(errors='replace'))
    destination.write_text('\n'.join(sections))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    if platform.system() != 'Darwin' or platform.machine() != 'arm64' or sys.version_info[:2] != (3, 11):
        raise SystemExit('Build on Apple Silicon macOS with Python 3.11.')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    backend = ROOT / 'desktop/backend'
    cli = ROOT / 'desktop/node_modules/.bin/tauri'
    if not cli.is_file():
        raise SystemExit('Run npm ci --prefix desktop first.')
    owned_remove(backend)
    with tempfile.TemporaryDirectory(prefix='localbrain-app-build-') as directory:
        work = Path(directory)
        env = {**os.environ, 'PYINSTALLER_CONFIG_DIR': str(work / 'cache')}
        run([sys.executable, '-m', 'PyInstaller', str(ROOT / 'desktop/backend.spec'), '--noconfirm',
             '--distpath', str(work / 'dist'), '--workpath', str(work / 'work')], cwd=ROOT, env=env)
        shutil.copytree(work / 'dist/localbrain-backend', backend, symlinks=True)
        (backend / MARKER).write_text('localbrain desktop build staging\n')
        generated_style = ROOT / 'desktop/ui/app-styles.css'
        shutil.copyfile(ROOT / 'src/localbrain/static/styles.css', generated_style)
        try:
            build_env = {key: value for key, value in os.environ.items() if key not in {'APPLE_ID', 'APPLE_PASSWORD', 'APPLE_TEAM_ID', 'APPLE_API_KEY', 'APPLE_API_ISSUER', 'APPLE_API_KEY_PATH'}}
            build_env = rust_build_environment(build_env, (Path.home(), ROOT, work))
            run([str(cli), 'build', '--target', 'aarch64-apple-darwin', '--bundles', 'app'], cwd=ROOT / 'desktop', env=build_env)
            built = ROOT / 'desktop/src-tauri/target/aarch64-apple-darwin/release/bundle/macos/LocalBrain.app'
            run(['codesign', '--verify', '--deep', '--strict', str(built)])
            # Output directories carry an explicit owner marker; arbitrary destinations are preserved.
            deliverable = output / 'LocalBrain-apple-silicon'
            owned_remove(deliverable)
            deliverable.mkdir()
            (deliverable / MARKER).write_text('localbrain standalone test distribution\n')
            app = deliverable / 'LocalBrain.app'
            run(['ditto', str(built), str(app)])
            shutil.copyfile(ROOT / 'docs/policies/project/standalone-test-app-guide.md', deliverable / 'READ-ME.md')
            third_party_notices(deliverable / 'THIRD-PARTY-NOTICES.txt')
            from datetime import datetime, timezone
            size = sum(p.stat().st_size for p in app.rglob('*') if p.is_file() and not p.is_symlink())
            version = plistlib.loads((app / 'Contents/Info.plist').read_bytes())['CFBundleShortVersionString']
            (deliverable / 'BUILD-INFO.md').write_text(
                '# LocalBrain test build\n\n' +
                '- Version: ' + version + '\n' +
                '- Built: ' + datetime.now(timezone.utc).isoformat() + '\n' +
                '- Build OS: macOS ' + platform.mac_ver()[0] + '\n' +
                '- Architecture: arm64; declared minimum macOS: 14\n' +
                '- Python: ' + platform.python_version() + '\n' +
                '- App bytes (regular files): ' + str(size) + '\n' +
                '- Signing: ad-hoc; notarization: not requested\n' +
                '- Builder checks: build, deep codesign verification and private build-path inspection\n' +
                '- Runtime/browser/teammate verification: record separately before distribution\n')
            check_bundle_paths(deliverable, app / 'Contents/Resources/backend/localbrain-backend', (Path.home(), ROOT, work))
            archive = output / 'LocalBrain-apple-silicon.zip'
            run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(deliverable), str(archive)])
            digest = hashlib.sha256()
            with archive.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(chunk)
            (output / 'LocalBrain-apple-silicon.sha256').write_text(digest.hexdigest() + '  ' + archive.name + '\n')
            print('Created:', archive)
        finally:
            generated_style.unlink(missing_ok=True)
            owned_remove(backend)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
