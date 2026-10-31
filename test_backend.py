import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import backend


class ProfilesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'profiles/work/sessions').mkdir(parents=True)
        (self.root / 'profiles/personal').mkdir()
        self.env = patch.dict(os.environ, {'PPI_PI_ROOT': str(self.root)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_list_default_and_delete_using_real_cli(self):
        self.assertEqual([p['name'] for p in backend.inventory()], ['personal', 'work'])
        result = backend.execute('set-default', 'work')
        self.assertTrue(next(p for p in result['profiles'] if p['name'] == 'work')['isDefault'])
        (self.root / 'profiles/work/sessions/session.json').write_text('test session')
        result = backend.execute('remove', 'work')
        self.assertEqual([p['name'] for p in result['profiles']], ['personal'])
        self.assertFalse((self.root / 'profiles/default.json').exists())
        self.assertFalse((self.root / 'profiles/work').exists())

    def test_invalid_and_missing_names(self):
        for name in ('../work', '--force', '', 'not-found', 'a' * 65):
            with self.assertRaises(ValueError):
                backend.execute('remove', name)
        self.assertTrue((self.root / 'profiles/work').exists())

    def test_launch_uses_arguments_not_shell(self):
        with patch.object(backend, 'inventory', return_value=[{'name': 'work'}]), \
             patch.object(backend, 'executable', side_effect=lambda n: '/bin/' + n), \
             patch.object(backend.subprocess, 'Popen') as spawn:
            spawn.return_value.wait.return_value = 0
            self.assertTrue(backend.execute('launch', 'work')['ok'])
            self.assertEqual(spawn.call_args.args[0], ['/bin/omarchy', 'launch', 'terminal', '/bin/ppi', 'use', 'work'])
            self.assertNotIn('shell', spawn.call_args.kwargs)
            self.assertTrue(spawn.call_args.kwargs['start_new_session'])
            for stream in ('stdin', 'stdout', 'stderr'):
                self.assertEqual(spawn.call_args.kwargs[stream], subprocess.DEVNULL)

    def test_two_launches_return_while_first_instance_is_alive(self):
        launcher = self.root / 'fake-launcher'
        launcher.write_text('#!/usr/bin/env python3\nimport time\ntime.sleep(2)\n')
        launcher.chmod(0o755)
        children = []
        real_spawn = subprocess.Popen
        def spawn(*args, **kwargs):
            child = real_spawn(*args, **kwargs)
            children.append(child)
            return child
        try:
            with patch.object(backend, 'inventory', return_value=[{'name': 'work'}]), \
                 patch.object(backend, 'executable', return_value=str(launcher)), \
                 patch.object(backend.subprocess, 'Popen', side_effect=spawn):
                started = time.monotonic()
                self.assertTrue(backend.execute('launch', 'work')['ok'])
                self.assertTrue(backend.execute('launch', 'work')['ok'])
                self.assertLess(time.monotonic() - started, 1.5)
                self.assertEqual(len(children), 2)
                self.assertTrue(all(child.poll() is None for child in children))
        finally:
            for child in children:
                child.terminate()
                child.wait(timeout=3)

    def test_cli_failure_is_reported(self):
        with patch.object(backend.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'broken config')):
            with self.assertRaisesRegex(ValueError, 'broken config'):
                backend.inventory()


if __name__ == '__main__':
    unittest.main()
