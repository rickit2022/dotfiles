# Portable dotfiles

One ordinary Git checkout stores selected settings for Linux and macOS. The
`dotfiles-sync` command copies only the files listed in `manifest.json` between
your home directory and this repository. Edit your usual live files, capture
them here, and explicitly sync to GitHub. The repository is not your home
directory, and no background job stages arbitrary files.

## Daily commands

```sh
dotfiles-sync status               # show live differences and Git status
dotfiles-sync capture --dry-run    # preview machine -> repository
dotfiles-sync capture              # save allowed live files locally
dotfiles-sync sync --dry-run       # preview; no network, commit or push
dotfiles-sync sync                 # capture, check, commit allowed files, push main
dotfiles-sync apply --dry-run      # preview repository -> machine
dotfiles-sync apply                # install configs, backing up replaced files
dotfiles-sync audit                # check publishable files for common credentials
```

`capture` does not stage, commit or contact GitHub. `sync` fetches `origin/main`
first and stops if the remote has changes you have not integrated. It refuses
an already staged index, stages only literal manifest filenames, scans the
outgoing history including later-deleted files, and never force pushes. A
missing source file is skipped, rather than deleting its saved copy.

The first migration of the repository structure is committed separately;
subsequent `sync` commands commit only selected configuration files. Changes
to the script, README, manifest or file removals require a normal explicit Git
commit. This keeps the daily command from sweeping up unrelated work.

If the remote has new commits, preserve your live changes first:

```sh
dotfiles-sync capture
cd ~/projects/dotfiles
git diff
git add -- files
git commit -m "Save local config changes"    # when there are changes to commit
git pull --rebase origin main                # resolve any conflicts normally
dotfiles-sync apply --dry-run
dotfiles-sync apply
dotfiles-sync sync
```

Authenticate with GitHub using `gh auth login` or your normal Git credential
helper/SSH agent. Keep credentials out of the remote URL. The configured remote
is `https://github.com/rickit2022/dotfiles.git`.

## Install on another machine

Install Git and Python 3.9 or newer. On macOS, Python can be installed with
Homebrew; the login shell may remain Zsh. Clone into a dedicated directory:

```sh
mkdir -p ~/projects
git clone https://github.com/rickit2022/dotfiles.git ~/projects/dotfiles
cd ~/projects/dotfiles
mkdir -p ~/.local/bin
ln -s "$PWD/dotfiles_sync.py" ~/.local/bin/dotfiles-sync
python3 dotfiles_sync.py apply --dry-run
python3 dotfiles_sync.py apply
```

If `~/.local/bin/dotfiles-sync` already exists, inspect it before creating the
link. Start a new terminal after applying. Applying never launches a new shell
or changes your default shell. No dependencies, system packages, credentials,
fonts or application state are installed automatically.

Replaced files are backed up under
`~/.local/state/dotfiles-sync/backups/TIMESTAMP/`, retaining their relative home
paths. Backups are local and excluded from syncing. To undo a change, copy its
backup to the original path. Missing files in the repository are skipped;
delete a previously applied file explicitly if you no longer want it.

## Shared settings and machine differences

Use one `main` branch for all hosts. Branches per host would require copying
every shared fix between branches. Keep shared settings in
`files/shared/`, OS-specific files in `files/linux/` or `files/darwin/`, and
select their platforms in the manifest. An individual file can live anywhere
under your home directory; its exact path must be listed.

`.bashrc` and `.zshrc` load `.config/shell/common.sh` for common aliases, PATH
entries and optional developer tools. History, prompt and completion settings
stay in their respective shells. Bash is not sourced from Zsh. The shared
loader detects Linux/macOS, finds Homebrew, and uses the appropriate Android
SDK location. NVM, pyenv and SDKMAN load only when installed. Existing desktop
or Keychain SSH agents are reused instead of starting an agent per terminal.

Keep host-only preferences and all secrets in ignored local overrides:

```text
~/.config/shell/local.sh    # Bash/Zsh environment overrides
~/.bashrc.local            # Bash-only settings
~/.zshrc.local             # Zsh-only settings
~/.profile.local           # login settings
~/.gitconfig.local         # identity, signing and credential-helper settings
```

Use a local Git identity if needed, for example with
`git config --file ~/.gitconfig.local user.email you@example.com`.
The old Linux `qwe` launcher remains optional on Linux. macOS ignores that
manifest entry; tmux and Neovim settings are shared across both platforms.

## What can be synced

The manifest currently contains shell startup/shared settings, Git preferences,
tmux, Neovim configuration and its plugin lockfile, plus the optional Linux
launcher. It lists individual regular UTF-8 files, not directory globs.
To manage another file, add an exact mapping and explicitly commit the manifest
and initial captured file:

```json
{
  "home": ".config/example/settings.conf",
  "repo": "files/shared/.config/example/settings.conf",
  "platforms": ["linux", "darwin"]
}
```

Credential stores, histories, local overrides, `.env` files, private key files,
Git internals and symlink paths are refused even if accidentally added to the
manifest. `.gitignore` provides another layer. Checks also reject common token
formats and literal secret assignments, naming the file without printing the
value. These checks are a precaution, not a guarantee that arbitrary file
contents are safe: add only reviewed configuration files. No credential
directory is scanned or copied by the capture command.

## Migration from this host's old setup

This checkout preserves the existing dotfiles Git history and remote. The old
home-root repository and live-file backups are retained locally; its oversized
object directory is not copied into this checkout or uploaded. The obsolete
hard-coded `dotfiles` Git alias and broken update script are replaced by the
`dotfiles-sync` command. `dotfiles` is a convenient shell alias for the same
command.

The current source tree omits the old font binaries and broad installation
scripts. Existing installed fonts and tools remain on the machine. Tool
installation is separate from syncing configuration; this avoids Linux-only
package actions being run on a Mac.

For more complex templating later, [chezmoi](https://www.chezmoi.io/user-guide/manage-machine-to-machine-differences/)
is an established alternative. Its [design documentation](https://www.chezmoi.io/user-guide/frequently-asked-questions/design/)
also favors a single branch with machine-specific settings. This small explicit
manifest meets the current need without introducing a dotfile-manager dependency.

## Verification

```sh
python3 -B -m unittest discover -s tests -v
```

Tests use temporary homes and local bare Git remotes. Bash and Zsh startup are
checked with Linux and macOS platform fixtures. Actual macOS startup should
also be previewed before applying on that machine.
