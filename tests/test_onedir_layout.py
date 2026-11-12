import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('beta_package_layout', ROOT / 'scripts/build_beta_package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)

class OnedirLayoutTests(unittest.TestCase):
    def test_build_mode(self):
        source = (ROOT / 'scripts/build_windows.py').read_text(encoding='utf-8-sig')
        self.assertIn("'--onedir'", source)
        self.assertNotIn("'--onefile'", source)
        self.assertIn("'--contents-directory', '_internal'", source)

    def test_installer_copies_tree_without_data_deletion(self):
        source = (ROOT / 'installer.iss').read_text(encoding='utf-8-sig')
        self.assertIn('Source: "dist\\IC35Thunderbird\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs', source)
        self.assertNotIn('[InstallDelete]', source)
        self.assertNotIn('[UninstallDelete]', source)

    def test_all_runtime_files_have_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / 'dist/IC35Thunderbird'
            (bundle / '_internal/sub').mkdir(parents=True)
            exe = bundle / 'IC35Thunderbird.exe'
            exe.write_bytes(b'synthetic executable')
            runtime = bundle / '_internal/sub/library.bin'
            runtime.write_bytes(b'synthetic runtime')
            empty = bundle / '_internal/empty-resource'
            empty.write_bytes(b'')
            result = package.collect_hashes(root, bundle, [exe])
            self.assertEqual(len(result), 3)
            self.assertEqual(result['dist/IC35Thunderbird/_internal/sub/library.bin'], hashlib.sha256(runtime.read_bytes()).hexdigest())
            self.assertIn('dist/IC35Thunderbird/_internal/empty-resource', result)

    def test_missing_runtime_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(RuntimeError, 'runtime folder'):
                package.collect_hashes(root, root / 'dist/IC35Thunderbird', [])

    def test_missing_required_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / 'dist/IC35Thunderbird'
            (bundle / '_internal').mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError, 'deliverable missing'):
                package.collect_hashes(root, bundle, [bundle / 'missing.exe'])

if __name__ == '__main__':
    unittest.main()
