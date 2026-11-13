"""The clone action must never attach GitHub credentials to another host."""
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import quote, urlsplit, urlunsplit

from test_audit_regressions import load_function


class GitCredentialScope(unittest.TestCase):
    def action(self, repo):
        return load_function('autogpt/commands/git_operations.py', 'clone_repository', {
            'Repo': repo, 'CFG': SimpleNamespace(github_username='fixture', github_api_key='dummy-fixture-token'),
            'path_in_workspace': lambda p: Path('/workspace') / p,
            'urlsplit': urlsplit, 'urlunsplit': urlunsplit, 'quote': quote, 're': re,
        })

    def test_rejects_other_hosts_and_ambiguous_urls_before_using_credentials(self):
        for url in ['https://attacker.invalid/owner/repo', 'http://github.com/owner/repo',
                    'https://github.com.attacker.invalid/owner/repo',
                    'https://github.com@attacker.invalid/owner/repo',
                    'https://github.com:444/owner/repo', 'file:///tmp/repo',
                    'ext::fixture', 'https://github.com/owner/repo?redirect=1']:
            repo = Mock()
            self.assertIn('Error:', self.action(repo)(url, 'clone'))
            repo.clone_from.assert_not_called()

    def test_normal_github_clone_retains_expected_destination(self):
        repo = Mock()
        result = self.action(repo)('https://github.com/owner/repository.git', 'clone')
        self.assertIn('Cloned', result)
        url, destination = repo.clone_from.call_args.args
        self.assertEqual(urlsplit(url).hostname, 'github.com')
        self.assertEqual(destination, Path('/workspace/clone'))

    def test_clone_error_does_not_return_credentials(self):
        repo = Mock()
        repo.clone_from.side_effect = RuntimeError('https://fixture:dummy-fixture-token@github.com/owner/repo')
        result = self.action(repo)('https://github.com/owner/repo', 'clone')
        self.assertIn('Error:', result)
        self.assertNotIn('dummy-fixture-token', result)


if __name__ == '__main__':
    unittest.main()
