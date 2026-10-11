import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'dotfiles_sync.py'


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.home = root / 'home'; self.home.mkdir()
        self.repo = root / 'repo'; self.repo.mkdir()
        git(self.repo, 'init', '-b', 'main')
        git(self.repo, 'config', 'user.name', 'Test')
        git(self.repo, 'config', 'user.email', 'test@example.invalid')
        (self.repo / 'README.md').write_text('Fixture\n')
        self.records = [dict(home='.bashrc', repo='files/shared/.bashrc'),
                        dict(home='.config/app/config.txt', repo='files/shared/config.txt'),
                        dict(home='linux.txt', repo='files/linux/config.txt', platforms=['linux']),
                        dict(home='mac.txt', repo='files/darwin/config.txt', platforms=['darwin'])]
        self.manifest()
        git(self.repo, 'add', 'README.md', 'manifest.json')
        git(self.repo, 'commit', '-m', 'Fixture')
        self.assertTrue(SCRIPT.exists(), 'The allowlisted dotfiles sync command is missing')
        spec = importlib.util.spec_from_file_location('dotfiles_sync', SCRIPT)
        self.module = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.module)
        self.sync = self.module.Dotfiles(self.repo, self.home, 'linux')

    def manifest(self):
        (self.repo / 'manifest.json').write_text(json.dumps({'version': 1, 'files': self.records}))

    def test_capture_uses_only_allowlist_and_current_platform(self):
        (self.home / '.bashrc').write_text('alias ll="ls -l"\n')
        (self.home / '.ssh').mkdir(); (self.home / '.ssh/id_rsa').write_text('private')
        (self.home / 'mac.txt').write_text('mac')
        (self.home / 'linux.txt').write_text('linux')
        self.sync.capture()
        self.assertEqual((self.repo / 'files/shared/.bashrc').read_text(), 'alias ll="ls -l"\n')
        self.assertTrue((self.repo / 'files/linux/config.txt').exists())
        self.assertFalse((self.repo / 'files/darwin/config.txt').exists())
        self.assertEqual(git(self.repo, 'diff', '--cached', '--name-only'), '')
        self.assertFalse((self.repo / '.ssh').exists())

    def test_secret_in_allowed_file_aborts_before_any_copy_and_hides_value(self):
        (self.home / '.bashrc').write_text('safe\n')
        secret = 'ghp_' + 'A' * 30
        path = self.home / '.config/app/config.txt'; path.parent.mkdir(parents=True)
        path.write_text('export API_TOKEN="' + secret + '"\n')
        with self.assertRaisesRegex(RuntimeError, 'credential') as error:
            self.sync.capture()
        self.assertNotIn(secret, str(error.exception))
        self.assertFalse((self.repo / 'files/shared/.bashrc').exists())

    def test_credential_scanner_allows_code_and_environment_references(self):
        self.module.check_text(SCRIPT.read_bytes(), 'sync command')
        self.module.check_text(b'export API_TOKEN="$API_TOKEN"\n', 'reference')
        self.module.check_text(b'secret_patterns = [\n', 'code')
        with self.assertRaisesRegex(RuntimeError, 'credential'):
            self.module.check_text(b'export PASSWORD="a password with spaces"\n', 'literal')

    def test_shell_terminators_do_not_hide_credential_assignments(self):
        for assignment in [b'export API_TOKEN="fixture_private_literal";',
                           b"TOKEN='fixture_private_literal'; echo done", b'PASSWORD=private_value;',
                           b'export PASSWORD="fixture#private"', b"PASSWORD='fixture#private'",
                           b'PASSWORD="private" # comment', b'PASSWORD=private # comment']:
            with self.subTest(assignment=assignment):
                with self.assertRaisesRegex(RuntimeError, 'credential'):
                    self.module.check_text(assignment, 'literal')

    def test_credential_paths_cannot_be_added_even_with_safe_contents(self):
        for path in ['.ssh/config', '.aws/config', '.codex/auth.json', '.config/gh/hosts.yml', '.env', '.git/config']:
            with self.subTest(path=path):
                self.records = [dict(home=path, repo='files/shared/unsafe')]; self.manifest()
                with self.assertRaisesRegex(RuntimeError, 'credential|private|Git'):
                    self.module.Dotfiles(self.repo, self.home, 'linux')

    def test_path_escape_and_symlink_sources_are_rejected(self):
        outside = self.home.parent / 'secret'; outside.write_text('safe-looking')
        (self.home / '.bashrc').symlink_to(outside)
        with self.assertRaisesRegex(RuntimeError, 'symlink'):
            self.sync.capture()
        self.records = [dict(home='../secret', repo='files/shared/config')]; self.manifest()
        with self.assertRaisesRegex(RuntimeError, 'relative'):
            self.module.Dotfiles(self.repo, self.home, 'linux')

    def test_apply_backs_up_existing_files_and_dry_run_does_not_write(self):
        (self.home / '.bashrc').write_text('old\n')
        source = self.repo / 'files/shared/.bashrc'; source.parent.mkdir(parents=True)
        source.write_text('new\n')
        self.sync.apply(dry_run=True)
        self.assertEqual((self.home / '.bashrc').read_text(), 'old\n')
        self.sync.apply()
        self.assertEqual((self.home / '.bashrc').read_text(), 'new\n')
        backups = list((self.home / '.local/state/dotfiles-sync/backups').glob('*/.bashrc'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'old\n')

    def test_sync_refuses_unrelated_staged_file_and_remote_new_commits(self):
        (self.repo / 'README.md').write_text('edited\n'); git(self.repo, 'add', 'README.md')
        with self.assertRaisesRegex(RuntimeError, 'staged'):
            self.sync.sync()
        git(self.repo, 'reset', '--', 'README.md'); git(self.repo, 'checkout', '--', 'README.md')
        remote = self.repo.parent / 'remote.git'; git(self.repo.parent, 'init', '--bare', str(remote))
        git(self.repo, 'remote', 'add', 'origin', str(remote)); git(self.repo, 'push', '-u', 'origin', 'main')
        peer = self.repo.parent / 'peer'; git(self.repo.parent, 'clone', '-b', 'main', str(remote), str(peer))
        git(peer, 'config', 'user.name', 'Peer'); git(peer, 'config', 'user.email', 'peer@example.invalid')
        (peer / 'README.md').write_text('remote update\n'); git(peer, 'add', 'README.md')
        git(peer, 'commit', '-m', 'Remote update'); git(peer, 'push', 'origin', 'main')
        with self.assertRaisesRegex(RuntimeError, 'remote.*new|Remote.*new'):
            self.sync.sync()

    def test_sync_commits_and_pushes_only_approved_files(self):
        remote = self.repo.parent / 'remote.git'; git(self.repo.parent, 'init', '--bare', str(remote))
        git(self.repo, 'remote', 'add', 'origin', str(remote)); git(self.repo, 'push', '-u', 'origin', 'main')
        (self.home / '.bashrc').write_text('updated\n')
        (self.repo / 'unrelated.txt').write_text('untouched\n')
        self.sync.sync(message='Sync approved configs')
        self.assertEqual(git(self.repo, 'show', '--format=', '--name-only', 'HEAD'), 'files/shared/.bashrc')
        self.assertEqual(git(self.repo, 'rev-parse', 'HEAD'), git(remote, 'rev-parse', 'main'))
        self.assertFalse('unrelated.txt' in git(self.repo, 'ls-files').splitlines())

    def test_deleted_secret_in_unpublished_history_is_never_pushed(self):
        remote = self.repo.parent / 'remote.git'; git(self.repo.parent, 'init', '--bare', str(remote))
        git(self.repo, 'remote', 'add', 'origin', str(remote)); git(self.repo, 'push', '-u', 'origin', 'main')
        previous = git(remote, 'rev-parse', 'main')
        secret = self.repo/'temporary.txt'; secret.write_text('ghp_'+'A'*30)
        git(self.repo,'add','temporary.txt'); git(self.repo,'commit','-m','Add then remove fixture')
        secret.unlink(); git(self.repo,'add','temporary.txt'); git(self.repo,'commit','-m','Remove fixture')
        with self.assertRaisesRegex(RuntimeError,'credential'):
            self.sync.sync()
        self.assertEqual(git(remote,'rev-parse','main'),previous)

    def test_unchanged_already_remote_binary_does_not_block_safe_updates(self):
        font=self.repo/'old-font.otf';font.write_bytes(b'old\x00font')
        git(self.repo,'add','old-font.otf');git(self.repo,'commit','-m','Old remote asset')
        remote=self.repo.parent/'remote.git';git(self.repo.parent,'init','--bare',str(remote))
        git(self.repo,'remote','add','origin',str(remote));git(self.repo,'push','-u','origin','main')
        (self.repo/'README.md').write_text('Safe intermediate update\n')
        git(self.repo,'add','README.md');git(self.repo,'commit','-m','Safe intermediate update')
        font.unlink();git(self.repo,'add','old-font.otf');git(self.repo,'commit','-m','Remove old asset')
        (self.home/'.bashrc').write_text('safe update\n')
        self.sync.sync()
        self.assertEqual(git(self.repo,'rev-parse','HEAD'),git(remote,'rev-parse','main'))

    def test_git_staging_treats_manifest_filenames_literally(self):
        self.records = [dict(home='.bashrc',repo='files/shared/config*')]; self.manifest()
        self.sync = self.module.Dotfiles(self.repo,self.home,'linux')
        remote = self.repo.parent / 'remote.git'; git(self.repo.parent,'init','--bare',str(remote))
        git(self.repo,'remote','add','origin',str(remote)); git(self.repo,'push','-u','origin','main')
        (self.home/'.bashrc').write_text('allowed')
        outside = self.repo/'files/shared/config-unapproved'; outside.parent.mkdir(parents=True)
        outside.write_text('not allowed')
        self.sync.sync()
        self.assertEqual(git(self.repo,'show','--format=','--name-only','HEAD'),'files/shared/config*')

    def test_repo_must_be_its_own_git_root(self):
        nested = self.repo / 'nested'; nested.mkdir()
        (nested / 'manifest.json').write_text((self.repo / 'manifest.json').read_text())
        with self.assertRaisesRegex(RuntimeError, 'repository root'):
            self.module.Dotfiles(nested, self.home, 'linux')


if __name__ == '__main__':
    unittest.main()
