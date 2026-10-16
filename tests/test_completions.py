"""Exercise completion in temporary shells without running either CLI."""
import os
from pathlib import Path
import pty
import select
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        shutil.copytree(ROOT / 'files/shared', self.home, dirs_exist_ok=True)
        bin_dir = self.home / 'bin'
        bin_dir.mkdir()
        for command in ('dotfiles-sync', 'codex-recovery'):
            path = bin_dir / command
            path.write_text('#!/bin/sh\nprintf "called\\n" >> "$HOME/unexpected-cli-calls"\n')
            path.chmod(0o755)
        self.env = {'HOME': str(self.home), 'PATH': str(bin_dir) + ':/usr/bin:/bin',
                    'TERM': 'xterm', 'LANG': 'C.UTF-8'}

    def bash_complete(self, *words):
        function = '_codex_recovery_complete' if words[0] == 'codex-recovery' else '_dotfiles_sync_complete'
        script = ('. "$HOME/.bashrc"; complete -p ' + shlex.quote(words[0]) +
                  ' >/dev/null || exit 1; COMP_WORDS=(' + ' '.join(map(shlex.quote, words)) +
                  '); COMP_CWORD=' + str(len(words)-1) + '; ' + function +
                  '; for reply in "${COMPREPLY[@]}"; do printf "%s\\0" "$reply"; done')
        result = subprocess.run(['bash', '--noprofile', '--norc', '-ic', script],
                                env=self.env, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertFalse((self.home / 'unexpected-cli-calls').exists())
        return [word for word in result.stdout.decode().split('\0') if word]

    def test_bash_subcommands_and_alias(self):
        for name in ('dotfiles-sync', 'dotfiles'):
            with self.subTest(command=name):
                self.assertEqual(set(self.bash_complete(name, '')),
                                 {'status', 'capture', 'apply', 'audit', 'sync', '--home', '-h', '--help'})
        self.assertEqual(set(self.bash_complete('codex-recovery', '')),
                         {'on', 'off', 'pause', 'attach', 'list', 'accounts', 'model', 'settings', 'status', 'run', 'check', '--config', '-h', '--help'})

    def test_bash_context_flags_with_global_option_values(self):
        cases = [
            (('dotfiles-sync', 'capture', '--d'), ['--dry-run']),
            (('dotfiles-sync', 'sync', '--m'), ['--message']),
            (('dotfiles-sync', 'status', '--d'), []),
            (('codex-recovery', 'run', '--'), ['--help', '--dry-run', '--json']),
            (('codex-recovery', 'check', '--j'), []),
            (('codex-recovery', 'status', '--j'), ['--json']),
            (('codex-recovery', 'pause', '--f'), []),
            (('codex-recovery', 'pause', '--'), ['--help']),
            (('codex-recovery', 'model', '--e'), ['--effort']),
            (('codex-recovery', 'model', '--f'), ['--follow']),
            (('codex-recovery', 'model', '--l'), ['--list']),
            (('codex-recovery', 'model', '--effort', ''), []),
            (('codex-recovery', 'settings', '--'), ['--help']),
            (('dotfiles-sync', '--home', 'sync', 'capture', '--d'), ['--dry-run']),
            (('codex-recovery', '--config', 'status', 'run', '--j'), ['--json']),
            (('dotfiles-sync', '--home=sync', 'capture', '--d'), ['--dry-run']),
            (('dotfiles-sync', '--home', '=', 'status', 'capture', '--d'), ['--dry-run']),
            (('codex-recovery', '--config', '=', 'check', 'run', '--j'), ['--json']),
        ]
        for words, expected in cases:
            with self.subTest(words=words):
                self.assertEqual(self.bash_complete(*words), expected)

    def test_bash_paths_with_spaces_and_message_values(self):
        directory = self.home / 'space home'
        directory.mkdir()
        file = self.home / 'config settings.json'
        file.write_text('{}')
        self.assertIn(str(directory)+'/', self.bash_complete('dotfiles-sync', '--home', str(self.home / 'spa')))
        self.assertIn(str(file), self.bash_complete('codex-recovery', '--config', str(self.home / 'con')))
        self.assertIn(str(file), self.bash_complete('codex-recovery', '--config', '=', str(self.home / 'con')))
        self.assertEqual(self.bash_complete('dotfiles-sync', 'sync', '--message', ''), [])

    def test_completion_files_are_managed_by_manifest(self):
        import json
        records = json.loads((ROOT / 'manifest.json').read_text())['files']
        homes = {entry['home'] for entry in records}
        self.assertTrue({'.config/shell/completions.bash', '.config/shell/completions.zsh'} <= homes)

    def test_zsh_real_tab_completion(self):
        executable = os.environ.get('DOTFILES_ZSH_TEST_COMMAND') or shutil.which('zsh')
        if not executable:
            self.skipTest('Zsh is not installed')
        self.env['FPATH'] = os.environ.get('DOTFILES_ZSH_TEST_FPATH', '')
        master, slave = pty.openpty()
        process = subprocess.Popen([executable, '-dfi'], env=self.env,
                                   stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
        os.close(slave)
        self.addCleanup(os.close, master)

        def stop():
            if process.poll() is None:
                process.kill()  # Interactive shells may ignore SIGTERM.
            process.wait(timeout=5)
        self.addCleanup(stop)
        pending = bytearray()

        def until(marker):
            deadline = time.monotonic() + 15
            while marker not in pending:
                remaining = deadline-time.monotonic()
                self.assertGreater(remaining, 0, pending.decode(errors='replace'))
                if select.select([master], [], [], min(remaining, 0.2))[0]:
                    pending.extend(os.read(master, 65536))
            end = pending.index(marker)+len(marker)
            result = bytes(pending[:end])
            del pending[:end]
            return result

        modules = os.environ.get('DOTFILES_ZSH_TEST_MODULES', '')
        setup = ('module_path=(' + shlex.quote(modules) + ' $module_path); ') if modules else ''
        setup += ('. "$HOME/.zshrc"; PS1="PROMPT> "; '
                  '_completion_dump() { print -r -- ""; print -r -- "__RESULT__${BUFFER}__END__"; BUFFER=""; CURSOR=0; zle reset-prompt; }; '
                  'zle -N _completion_dump; bindkey "^X" _completion_dump; printf "__READY__\\n"\n')
        os.write(master, setup.encode())
        until(b'__READY__\r\n')
        directory = self.home / 'space home'
        directory.mkdir()
        config = self.home / 'config settings.json'
        config.write_text('{}')
        cases = [
            ('dotfiles-sync ca', 'dotfiles-sync capture '),
            ('dotfiles sy', 'dotfiles sync '),
            ('codex-recovery ac', 'codex-recovery accounts '),
            ('codex-recovery mo', 'codex-recovery model '),
            ('codex-recovery se', 'codex-recovery settings '),
            ('codex-recovery model --e', 'codex-recovery model --effort '),
            ('codex-recovery model --f', 'codex-recovery model --follow '),
            ('codex-recovery run --j', 'codex-recovery run --json '),
            ('codex-recovery pa', 'codex-recovery pause '),
            ('codex-recovery pause --h', 'codex-recovery pause --help '),
            ('dotfiles-sync --home sync capture --d', 'dotfiles-sync --home sync capture --dry-run '),
            ('codex-recovery --config status run --j', 'codex-recovery --config status run --json '),
            ('dotfiles-sync --home '+str(self.home/'spa'), 'dotfiles-sync --home '+str(directory).replace(' ', '\\ ')+'/'),
            ('codex-recovery --config '+str(self.home/'con'), 'codex-recovery --config '+str(config).replace(' ', '\\ ')+' '),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                os.write(master, text.encode()+b'\t\x18')
                result = until(b'__END__\r\n').decode(errors='replace')
                actual = result.rsplit('__RESULT__', 1)[1].split('__END__', 1)[0]
                self.assertEqual(actual, expected, result)
        self.assertFalse((self.home/'unexpected-cli-calls').exists())


if __name__ == '__main__':
    unittest.main()
