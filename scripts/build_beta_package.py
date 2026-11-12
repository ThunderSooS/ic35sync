"""Build a versioned onedir beta package from the directly integrated main source.
Version labels and source-package allowlist are adjusted only in the build checkout.
No Git push, tag, release publication or real device access is performed.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

VERSION = '3.4.0b7'


def prepare_sources(root):
    replacements = {
        'app.py': [("VERSION = '3.4.0b6'", "VERSION = '3.4.0b7'")],
        'installer.iss': [('#define AppVersion "3.4.0b6"', '#define AppVersion "3.4.0b7"')],
        'scripts/package_source.py': [
            ("VERSION = '3.4.0b6'", "VERSION = '3.4.0b7'"),
            ("'memo_sync.py']", "'memo_sync.py', 'task_delete_metadata.py', 'diagnose_tasks.py']")]
    }
    prepared = {}
    for name, changes in replacements.items():
        text = (root / name).read_text(encoding='utf-8-sig')
        for old, new in changes:
            if text.count(old) == 1 and text.count(new) == 0:
                text = text.replace(old, new)
            elif text.count(old) != 0 or text.count(new) != 1:
                raise RuntimeError('Unexpected version or package structure: ' + name)
        if name.endswith('.py'):
            compile(text, name, 'exec')
        prepared[name] = text
    sync = (root / 'dav_sync.py').read_text(encoding='utf-8-sig')
    tree = ast.parse(sync)
    imports = [n for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == 'task_delete_metadata']
    if len(imports) != 1 or '_remote_unchanged_for_delete(r, binding)' not in sync:
        raise RuntimeError('Permanent task deletion fix is not integrated')
    for name in ('task_delete_metadata.py', 'diagnose_tasks.py'):
        if not (root / name).is_file():
            raise RuntimeError('Missing source: ' + name)
    for name, text in prepared.items():
        (root / name).write_bytes(text.encode('utf-8'))
    return sorted(prepared)


def run(root, *args, timeout=1200):
    subprocess.run(list(args), cwd=root, check=True, timeout=timeout)


def collect_hashes(root, bundle, required):
    if not (bundle / '_internal').is_dir():
        raise RuntimeError('Onedir runtime folder missing')
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError('Required deliverable missing: ' + path.name)
    paths = {path for path in bundle.rglob('*') if path.is_file()} | set(required)
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def main():
    root = Path(__file__).resolve().parents[1]
    if sys.platform != 'win32':
        raise RuntimeError('Windows build runner required')
    changed = prepare_sources(root)
    run(root, sys.executable, 'scripts/build_windows.py')
    checks = json.loads((root / 'smoke-results.json').read_text(encoding='utf-8'))
    if checks.get('version') != VERSION:
        raise RuntimeError('Built EXE version does not match beta package version')
    shutil.copyfile(root / 'smoke-results.json', root / 'smoke-results-exe.json')
    compiler = shutil.which('ISCC.exe')
    if not compiler:
        program_files = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'))
        matches = sorted(program_files.glob('Inno Setup */ISCC.exe'), reverse=True)
        compiler = str(matches[0]) if matches else None
    if not compiler:
        raise RuntimeError('Inno Setup compiler not installed')
    run(root, compiler, '/DBuildTest=1', 'installer.iss', timeout=300)
    run(root, sys.executable, 'scripts/test_installer.py', timeout=300)
    run(root, compiler, 'installer.iss', timeout=300)
    run(root, sys.executable, 'scripts/package_source.py', timeout=300)
    release = root / 'release'
    source_zip = release / f'IC35-Sync-Beta-{VERSION}-Source.zip'
    with zipfile.ZipFile(source_zip) as archive:
        prefix = f'IC35-Thunderbird-{VERSION}/'
        for name in ('task_delete_metadata.py', 'diagnose_tasks.py', 'dav_sync.py', 'app.py', 'installer.iss'):
            if archive.read(prefix + name) != (root / name).read_bytes():
                raise RuntimeError('Source archive does not match build checkout: ' + name)
    bundle = root / 'dist/IC35Thunderbird'
    required = [bundle / 'IC35Thunderbird.exe',
                release / f'IC35-Sync-Beta-{VERSION}-Setup.exe', source_zip,
                release / 'IC35-Thunderbird-Bridge-3.4.0b5.xpi']
    hashes = collect_hashes(root, bundle, required)
    manifest = {
        'version': VERSION, 'bundle_mode': 'onedir',
        'repository_commit': os.environ.get('GITHUB_SHA', 'local'),
        'build_checkout_changes': changed,
        'sync_logic_modified_during_build': False,
        'version_and_package_allowlist_adjusted_in_build_checkout': True,
        'unit_tests_and_exe_smoke_checks': 'passed',
        'isolated_test_installer_install_and_uninstall': 'passed',
        'installed_runtime_files_verified_by_sha256': True,
        'production_installer_installation': 'not performed',
        'release_published': False, 'real_device_test_in_this_build': 'not performed',
        'sha256': hashes
    }
    (release / 'BUILD-MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (release / 'SHA256SUMS.txt').write_text(''.join(digest + '  ' + name + '\n' for name, digest in sorted(hashes.items())), encoding='utf-8')
    (release / 'START-HERE.txt').write_text(
        'IC35 Sync Beta 3.4.0b7 - ONEDIR BUILD\n'
        'Recommended: run IC35-Sync-Beta-3.4.0b7-Setup.exe from this release folder.\n'
        'For manual use, keep the ENTIRE dist/IC35Thunderbird folder together.\n'
        'IC35Thunderbird.exe requires its _internal folder. Do not copy only the EXE.\n'
        'Close IC35 Sync before installing and keep your data backups.\n'
        'This build does not change sync logic or disable antivirus.\n'
        'Startup improvement on the user computer has not yet been measured.\n'
        'This package is not automatically published as a GitHub release.\n', encoding='utf-8')
    diff = subprocess.run(['git', 'diff', '--', 'app.py', 'installer.iss', 'scripts/package_source.py', 'build-requirements.txt'],
                          cwd=root, check=True, capture_output=True).stdout
    (release / 'BUILD-CHECKOUT.diff').write_bytes(diff)
    print('Onedir beta package built and checked:', VERSION)


if __name__ == '__main__':
    main()
