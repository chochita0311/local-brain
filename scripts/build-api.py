#!/usr/bin/env python3
"""Build the native macOS API/CLI plus public web assets; Python is build tooling only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/desktop'))
from build_support import BUILD_OUTPUT_MARKER, check_bundle_paths, rust_build_environment, source_identity


def cargo_artifacts(output, expected):
    artifacts = {}
    for line in output.splitlines():
        message = json.loads(line)
        target = message.get('target', {})
        name = target.get('name')
        if message.get('reason') == 'compiler-artifact' and name in expected and 'bin' in target.get('kind', []):
            executable = Path(message.get('executable') or '')
            if name in artifacts or not executable.is_absolute() or not executable.is_file():
                raise ValueError('Cargo did not identify one absolute executable per requested binary')
            artifacts[name] = executable
    if set(artifacts) != set(expected):
        raise ValueError('Cargo did not produce every requested binary')
    return artifacts


def check_output(path):
    path = path.expanduser().absolute()
    if path.is_symlink():
        raise ValueError('Refusing to replace a linked native build')
    if path.exists() and (not path.is_dir() or not (path / BUILD_OUTPUT_MARKER).is_file()
                          or (path / BUILD_OUTPUT_MARKER).is_symlink()):
        raise ValueError('Refusing to replace an unowned native build')
    return path


def third_party_notices(destination, manifests=None):
    sections = ['LocalBrain native dependency notices\n\nPublic model weights are not included.\n']
    for relative in ('apps/api/resources/LICENSE-fastapi.txt',
                     'crates/core/src/backend/html/LICENSE-PSF.txt'):
        sections.append('\n## Bundled source: ' + relative + '\n' + (ROOT / relative).read_text())
    seen = set()
    for manifest in manifests or [ROOT / 'Cargo.toml']:
        metadata = json.loads(subprocess.check_output(
            ['cargo', 'metadata', '--locked', '--offline', '--format-version', '1', '--manifest-path', str(manifest)], text=True))
        for package in sorted(metadata['packages'], key=lambda item: (item['name'], item['version'])):
            identity = (package['name'], package['version'])
            if not package['source'] or identity in seen:
                continue
            seen.add(identity)
            sections.append('\n## Rust: ' + ' '.join(identity) + '\n' + (package.get('license') or 'See upstream license files.'))
            folder = Path(package['manifest_path']).parent
            files = {path for path in folder.iterdir() if path.is_file() and path.name.lower().startswith(('license', 'licence', 'copying', 'notice', 'copyright'))}
            if package.get('license_file'):
                files.add(folder / package['license_file'])
            for path in sorted(files):
                if path.is_file():
                    sections.append('\n' + path.read_text(errors='replace'))
    destination.write_text('\n'.join(sections))


def finalize(root):
    """Record executable bytes after the desktop packager's final signing."""
    receipt_path = root / 'BUILD-INFO.json'
    receipt = json.loads(receipt_path.read_text())
    folder = root if receipt['edition'] == 'desktop' else root / 'bin'
    receipt['executables'] = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                              for name in receipt['executables']}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def build(destination, *, desktop=False, terminal_bundle=None):
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise ValueError('Build this native artifact on Apple Silicon macOS')
    destination = check_output(destination)
    identity = source_identity(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    binaries = ['localbrain-backend'] if desktop else ['localbrain', 'lb']
    with tempfile.TemporaryDirectory(prefix='.native-api-build-', dir=destination.parent) as temporary:
        work = Path(temporary)
        candidate = work / 'native'
        candidate.mkdir()
        env = rust_build_environment(os.environ, (Path.home(), ROOT, work))
        env['MACOSX_DEPLOYMENT_TARGET'] = '14.0'
        command = ['cargo', 'build', '--locked', '--release', '--target', 'aarch64-apple-darwin',
                   '-p', 'localbrain-api', '--message-format=json-render-diagnostics', '--manifest-path', str(ROOT / 'Cargo.toml')]
        for name in binaries:
            command += ['--bin', name]
        compiled = subprocess.run(command, check=True, env=env, capture_output=True, text=True)
        artifacts = cargo_artifacts(compiled.stdout, binaries)
        output_root = candidate if desktop else candidate / 'bin'
        output_root.mkdir(exist_ok=True)
        for name, executable in artifacts.items():
            if subprocess.check_output(['/usr/bin/lipo', '-archs', str(executable)], text=True).strip() != 'arm64':
                raise ValueError('The backend is not the declared arm64 target')
            target = output_root / name
            shutil.copyfile(executable, target)
            target.chmod(0o700)
            subprocess.run(['codesign', '--force', '--sign', '-', str(target)], check=True, capture_output=True)
        shutil.copytree(ROOT / 'apps/web', candidate / 'web')
        if terminal_bundle is not None:
            if desktop:
                raise ValueError('The desktop shell owns its separate terminal resource')
            shutil.copytree(terminal_bundle, candidate / 'terminal/runtime')
        third_party_notices(candidate / 'THIRD-PARTY-NOTICES.txt')
        final = source_identity(ROOT)
        if any(final[key] != identity[key] for key in ('commit', 'input_sha256')):
            raise ValueError('Native build inputs changed during packaging; rebuild the current source')
        receipt = {'schema': 1, 'backend': 'rust', 'edition': 'desktop' if desktop else 'web',
                   'target': 'aarch64-apple-darwin', 'minimumOs': '14.0', 'source': identity,
                   'rust': subprocess.check_output(['rustc', '--version'], text=True).strip(),
                   'executables': {name: hashlib.sha256((output_root / name).read_bytes()).hexdigest() for name in binaries}}
        (candidate / 'BUILD-INFO.json').write_text(json.dumps(receipt, indent=2) + '\n')
        (candidate / BUILD_OUTPUT_MARKER).write_text('localbrain native build\n')
        check_bundle_paths(candidate, output_root / binaries[0], (Path.home(), ROOT, work))
        check_output(destination)
        backup = destination.with_name('.' + destination.name + '.previous-' + uuid.uuid4().hex)
        if destination.exists():
            destination.rename(backup)
        try:
            candidate.rename(destination)
        except BaseException:
            if backup.exists() and not destination.exists():
                backup.rename(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/api')
    parser.add_argument('--desktop', action='store_true')
    parser.add_argument('--terminal-bundle', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output, desktop=args.desktop, terminal_bundle=args.terminal_bundle), indent=2))


if __name__ == '__main__':
    main()
