#!/usr/bin/env python3
"""Capture and restore an explicit set of dotfiles using an ordinary Git repo."""
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
PRIVATE_PARTS = {'.git', '.ssh', '.aws', '.gnupg', '.codex', '.claude', '.gemini',
                 '.docker', 'keyrings', 'credentials', 'gh', 'gcloud', 'op'}
SECRET_PATTERNS = [
    re.compile(r'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----'),
    re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|'
               r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}|(?:AKIA|ASIA)[0-9A-Z]{16})'),
    re.compile(r'https?://[^\s/]+:[^\s/@]+@'),
    re.compile(r'(?i)authorization\s*[:=]\s*["\']?(?:bearer|basic)\s+[A-Za-z0-9+/=_-]{12,}'),
]
ASSIGNMENT = re.compile(r'(?im)^\s*(?:export\s+)?([\w.-]*(?:token|secret|password|passwd|api[_-]?key)[\w.-]*)'
                        r'\s*[=:]\s*([^\n]+)')
JSON_SECRET = re.compile(r'(?i)["\'](?:access_token|refresh_token|api_key|password|client_secret)["\']'
                         r'\s*:\s*(["\'][^"\']+["\'])')


def safe_relative(value):
    if not isinstance(value, str) or not value or '\\' in value or any(ord(c) < 32 for c in value):
        raise RuntimeError('Manifest paths must be safe relative paths')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ('.', '..') for part in value.split('/')):
        raise RuntimeError('Manifest paths must be safe relative paths')
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if (parts & PRIVATE_PARTS or name == '.env' or name.startswith('.env.')
            or name.endswith(('.local', '.pem', '.key', '.p12', '.pfx', '.kdbx'))
            or name in {'auth.json', 'hosts.yml', '.netrc', '.npmrc', '.pypirc', '.git-credentials', 'local.sh'}
            or name in {'.netrwhist', '.viminfo'} or 'shada' in parts
            or any(part.endswith('_history') or part in {'history', '.bash_history', '.zsh_history'} for part in parts)):
        raise RuntimeError('Manifest cannot sync private credential, Git, history or local override paths')
    return path


def checked_path(root, relative):
    path = root / relative
    for parent in [path, *path.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise RuntimeError('Refusing symlink in managed path: ' + str(relative))
    if not path.resolve().is_relative_to(root.resolve()):
        raise RuntimeError('Managed path escaped its root: ' + str(relative))
    return path


def check_text(data, label):
    if len(data) > 1024 * 1024 or b'\0' in data:
        raise RuntimeError('Only text configs up to 1 MiB may be synced: ' + str(label))
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        raise RuntimeError('Only UTF-8 text configs may be synced: ' + str(label)) from None
    suspicious = any(pattern.search(text) for pattern in SECRET_PATTERNS)
    values = [m.group(2) for m in ASSIGNMENT.finditer(text)] + [m.group(1) for m in JSON_SECRET.finditer(text)]
    for value in values:
        value = value.strip()
        quoted = re.match(r'(["\'])([^"\'\n]*)\1\s*(?:;|#|$)', value)
        if quoted:
            value = quoted.group(2)
        else:
            bare = re.match(r'([^\s;\'"(){}\[\],]+)\s*(?:;|#|$)', value)
            if not bare:
                continue  # Code expressions and referenced values are not literal credentials.
            value = bare.group(1)
        if value and not value.startswith(('$', '<', 'YOUR_', 'your_', 'REPLACE_', 'replace_')):
            suspicious = True
    if suspicious:
        raise RuntimeError('Possible credential in ' + str(label) + '; move it to an ignored local file')
    if re.search(r'/(?:home|Users)/(?!USER(?:NAME)?(?:/|\b))[^\s/"\'<>:]+', text):
        raise RuntimeError('Private home path in ' + str(label) + '; use $HOME, ~ or a local override')
    if Path(str(label).split(' in unpublished ', 1)[0]).name == '.gitconfig' and re.search(r'(?im)^\s*email\s*=', text):
        raise RuntimeError('Git email identity in ' + str(label) + '; keep it in ~/.gitconfig.local')


def write_file(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        temporary.chmod(mode)
        temporary.replace(path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


class Dotfiles:
    def __init__(self, repo=ROOT, home=None, platform=None):
        self.repo = Path(repo).resolve()
        self.home = Path(home or Path.home()).resolve()
        self.platform = platform or ('darwin' if sys.platform == 'darwin' else 'linux' if sys.platform.startswith('linux') else sys.platform)
        if Path(self.git('rev-parse', '--show-toplevel')).resolve() != self.repo:
            raise RuntimeError('Run from the dedicated dotfiles repository root, not the home Git repository')
        manifest = json.loads(checked_path(self.repo, 'manifest.json').read_text())
        if manifest.get('version') != 1 or not isinstance(manifest.get('files'), list):
            raise RuntimeError('Unsupported dotfiles manifest')
        self.files = []; homes = set(); targets = set()
        for item in manifest['files']:
            home_path, repo_path = safe_relative(item.get('home')), safe_relative(item.get('repo'))
            if not str(repo_path).startswith('files/'):
                raise RuntimeError('Managed repository paths must be inside files/')
            platforms = item.get('platforms', ['linux', 'darwin'])
            if not isinstance(platforms, list) or not platforms or any(p not in ('linux', 'darwin') for p in platforms):
                raise RuntimeError('Manifest platforms must be linux and/or darwin')
            if self.platform not in platforms:
                continue
            if home_path in homes or repo_path in targets:
                raise RuntimeError('Duplicate managed path in manifest')
            homes.add(home_path); targets.add(repo_path)
            self.files.append((home_path, repo_path))
        if not self.files:
            raise RuntimeError('No managed files for this operating system')

    def git(self, *args, binary=False):
        environment = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_LITERAL_PATHSPECS='1')
        result = subprocess.run(['git', '-C', str(self.repo), *args], env=environment,
                                capture_output=True, text=not binary, timeout=90)
        if result.returncode:
            # Git errors can include a credential-bearing remote URL or hook output.
            raise RuntimeError('Git ' + args[0] + ' failed (exit ' + str(result.returncode) + '). Inspect it in this repository.')
        return result.stdout if binary else result.stdout.strip()

    @contextmanager
    def locked(self):
        git_dir = Path(self.git('rev-parse', '--absolute-git-dir'))
        with (git_dir / 'dotfiles-sync.lock').open('a') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Another dotfiles sync is already running') from None
            yield

    def changes(self, apply=False):
        changes = []
        for home_relative, repo_relative in self.files:
            home_path = checked_path(self.home, home_relative)
            repo_path = checked_path(self.repo, repo_relative)
            source, target = (repo_path, home_path) if apply else (home_path, repo_path)
            if not source.exists():
                continue  # A missing file never silently deletes a saved configuration.
            if not source.is_file() or (target.exists() and not target.is_file()):
                raise RuntimeError('Managed paths must be regular files: ' + str(home_relative))
            data = source.read_bytes(); check_text(data, home_relative)
            mode = 0o755 if source.stat().st_mode & 0o111 else 0o644
            if target.exists() and target.read_bytes() == data and bool(target.stat().st_mode & 0o111) == bool(mode & 0o111):
                continue
            changes.append((home_relative, repo_relative, target, data, mode))
        return changes

    def capture(self, dry_run=False):
        changes = self.changes()
        for home_path, repo_path, target, data, mode in changes:
            print(('Would capture: ' if dry_run else 'Capture: ') + str(home_path) + ' -> ' + str(repo_path))
            if not dry_run:
                write_file(target, data, mode)
        if not changes:
            print('Managed files are already captured.')
        return [str(item[1]) for item in changes]

    def apply(self, dry_run=False):
        changes = self.changes(apply=True)
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup = checked_path(self.home, '.local/state/dotfiles-sync/backups/' + stamp)
        for home_path, _, target, data, mode in changes:
            print(('Would apply: ' if dry_run else 'Apply: ') + str(home_path))
            if not dry_run:
                if target.exists():
                    write_file(backup / home_path, target.read_bytes(), 0o600)
                write_file(target, data, mode)
        if changes and not dry_run:
            print('Backups: ' + str(backup))
        if not changes:
            print('Managed files already match the repository.')

    def audit(self):
        paths = self.git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0')
        for name in filter(None, paths):
            path = checked_path(self.repo, name)
            safe_relative(name)
            if path.exists():
                if not path.is_file():
                    raise RuntimeError('Only regular files may be published: ' + name)
                check_text(path.read_bytes(), name)
        print('Credential checks passed for publishable repository files.')

    def audit_outgoing(self):
        # Existing remote blobs are already published. Check every new blob,
        # including ones introduced and later removed in unpublished commits.
        seen = {entry.split('\t', 1)[0].split()[2] for entry in
                filter(None, self.git('ls-tree', '-r', '-z', 'origin/main').split('\0'))}
        commits = self.git('rev-list', 'origin/main..HEAD').splitlines()
        for commit in commits:
            for entry in filter(None, self.git('ls-tree', '-r', '-z', commit).split('\0')):
                metadata, name = entry.split('\t', 1)
                mode, kind, blob = metadata.split()
                safe_relative(name)
                if kind != 'blob' or mode not in ('100644', '100755'):
                    raise RuntimeError('Only regular files may be published: ' + name)
                if blob not in seen:
                    if int(self.git('cat-file', '-s', blob)) > 1024 * 1024:
                        raise RuntimeError('Only text configs up to 1 MiB may be published: ' + name)
                    check_text(self.git('cat-file', 'blob', blob, binary=True), name+' in unpublished '+commit[:8])
                    seen.add(blob)
        print('Credential checks passed for unpublished Git history.')

    def sync(self, dry_run=False, message=None):
        if self.git('diff', '--cached', '--name-only'):
            raise RuntimeError('Unrelated or existing staged changes; commit or unstage them before sync')
        if self.git('branch', '--show-current') != 'main':
            raise RuntimeError('Use the shared main branch for dotfiles sync')
        remote = self.git('remote', 'get-url', 'origin')
        if re.search(r'https?://[^\s/]+@', remote):
            raise RuntimeError('Keep credentials out of the Git remote URL')
        if dry_run:
            self.capture(dry_run=True); self.audit()
            print('Dry run: no commit, fetch or push performed.'); return
        self.git('fetch', 'origin', 'main')
        try:
            self.git('merge-base', '--is-ancestor', 'origin/main', 'HEAD')
        except RuntimeError:
            raise RuntimeError('Remote has new commits. Capture locally, review git diff, commit, then git pull --rebase; never force push.') from None
        self.capture()
        self.audit()
        allowed = [str(path) for _, path in self.files]
        candidates = set(self.git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0'))
        existing = [path for path in allowed if path in candidates and (self.repo / path).exists()]
        if existing:
            self.git('add', '--', *existing)
        if self.git('diff', '--cached', '--name-only'):
            self.git('commit', '-m', message or 'Sync configs')
        self.audit_outgoing()
        self.git('push', 'origin', 'HEAD:main')
        print('Synced selected configs to origin/main.')

    def status(self):
        print('Repository: ' + str(self.repo))
        print('Platform: ' + self.platform + '; ' + str(len(self.files)) + ' explicitly allowed files')
        self.capture(dry_run=True)
        state = self.git('status', '--short')
        print(state or 'Git working tree is clean.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, help='alternate home directory for testing or installation')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('status', 'capture', 'apply', 'audit', 'sync'):
        child = sub.add_parser(command)
        if command in ('capture', 'apply', 'sync'):
            child.add_argument('--dry-run', action='store_true')
        if command == 'sync':
            child.add_argument('-m', '--message')
    args = parser.parse_args()
    try:
        dotfiles = Dotfiles(home=args.home)
        if args.command in ('status', 'audit'):
            getattr(dotfiles, args.command)()
        else:
            with dotfiles.locked():
                options = {'dry_run':args.dry_run}
                if args.command == 'sync':
                    options['message'] = args.message
                getattr(dotfiles, args.command)(**options)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print('Error: ' + str(error), file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
