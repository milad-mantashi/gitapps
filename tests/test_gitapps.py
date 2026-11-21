import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError
import gitapps
import install


class GitAppsTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(gitapps.compare('1.6.0', 'v1.7.0'), 'Update available')
        self.assertEqual(gitapps.compare('1.18.2+64', 'v1.18.2'), 'Up to date')
        self.assertEqual(gitapps.compare('1.2', '1.2.0'), 'Up to date')
        self.assertIn('Cannot compare', gitapps.compare('1.0-rc1', '1.0'))

    def test_happ_package(self):
        with patch('gitapps.shutil.which', side_effect=lambda name: '/bin/dpkg-query' if name == 'dpkg-query' else None), patch('gitapps.run_local', return_value='install ok installed\t4.7.2-341') as run:
            self.assertEqual(gitapps.detect_installed('Happ-proxy/happ-desktop')[0], '4.7.2')
            self.assertEqual(run.call_args.args[0][-1], 'happ')

    def test_registry(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {'XDG_CONFIG_HOME': root}):
            state = gitapps.load_state()
            state['owner/tool'] = {'current': None}
            gitapps.save_state(state)
            self.assertIn('owner/tool', gitapps.load_state())
            gitapps.state_path().write_text('invalid json')
            with self.assertRaises(ValueError):
                gitapps.load_state()

    def test_notice_and_unknown(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'tag_name': 'v2.0.0'}).encode()
        for installed in ['1.0.0', None]:
            output = io.StringIO()
            with patch('gitapps.detect_installed', return_value=(installed, 'test')), patch('gitapps.urlopen', return_value=response), contextlib.redirect_stdout(output):
                self.assertEqual(gitapps.check_release('owner/tool'), 0)
            self.assertIn('Download it from' if installed else 'cannot be confirmed', output.getvalue())

    def test_network_error(self):
        with patch('gitapps.detect_installed', return_value=(None, 'test')), patch('gitapps.urlopen', side_effect=URLError('offline')), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(gitapps.check_release('owner/tool'), 1)

    def test_installer(self):
        with tempfile.TemporaryDirectory() as root, patch('install.Path.home', return_value=Path(root)), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(install.main(), 0)
            self.assertEqual(install.main(), 0)
            target = Path(root) / '.local/bin/gitapps'
            self.assertTrue(target.is_symlink())
            target.unlink()
            target.write_text('keep')
            self.assertEqual(install.main(), 1)
            self.assertEqual(target.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
