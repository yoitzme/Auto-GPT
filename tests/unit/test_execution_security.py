"""Provider-free checks of the production command bodies; no shell or Docker starts."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from test_audit_regressions import load_function


class ExecutionSecurity(unittest.TestCase):
    def test_disabled_background_shell_does_not_start_process(self):
        process = Mock()
        run = load_function('autogpt/commands/execute_code.py', 'execute_shell_popen', {
            'CFG': SimpleNamespace(execute_local_commands=False),
            'os': os, 'WORKSPACE_PATH': Path.cwd(), 'subprocess': process,
        })
        result = run('echo fixture')
        self.assertIn('not allowed', result)
        process.Popen.assert_not_called()

    def test_allowed_shell_returns_output_without_changing_process_directory(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            process = Mock()
            process.run.return_value = SimpleNamespace(stdout=b'fixture', stderr=b'')
            run = load_function('autogpt/commands/execute_code.py', 'execute_shell', {
                'CFG': SimpleNamespace(execute_local_commands=True),
                'os': os, 'WORKSPACE_PATH': Path(directory), 'subprocess': process,
            })
            self.assertIn('fixture', run('echo fixture'))
            self.assertEqual(process.run.call_args.kwargs['cwd'], Path(directory))
            self.assertEqual(Path.cwd(), previous)

    def test_shell_failure_does_not_change_global_working_directory(self):
        previous = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                process = Mock()
                process.run.side_effect = OSError('fixture failure')
                run = load_function('autogpt/commands/execute_code.py', 'execute_shell', {
                    'CFG': SimpleNamespace(execute_local_commands=True),
                    'os': os, 'WORKSPACE_PATH': Path(directory), 'subprocess': process,
                })
                with self.assertRaises(OSError):
                    run('fixture')
                self.assertEqual(Path.cwd(), previous)
        finally:
            os.chdir(previous)

    def test_python_filename_is_one_argument_not_shell_text(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = 'space ; echo injected.py'
            file = Path(directory) / filename
            file.write_text('print("fixture")')
            process = Mock()
            process.run.return_value = SimpleNamespace(returncode=0, stdout='fixture', stderr='')
            run = load_function('autogpt/commands/execute_code.py', 'execute_python_file', {
                'os': os, 'WORKSPACE_PATH': Path(directory), 'subprocess': process,
                'path_in_workspace': lambda _: file,
                'we_are_running_in_a_docker_container': lambda: True,
            })
            self.assertEqual(run(filename), 'fixture')
            args, kwargs = process.run.call_args
            self.assertEqual(args[0], ['python', str(file)])
            self.assertFalse(kwargs.get('shell', False))


if __name__ == '__main__':
    unittest.main()
