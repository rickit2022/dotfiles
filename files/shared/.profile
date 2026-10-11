# POSIX login environment. macOS Zsh uses .zshrc instead.
for dotfiles_bin in "$HOME/.local/bin" "$HOME/bin" "$HOME/development/flutter/bin"; do
    if [ -d "$dotfiles_bin" ]; then
        case ":$PATH:" in *":$dotfiles_bin:"*) ;; *) PATH="$dotfiles_bin:$PATH" ;; esac
    fi
done
unset dotfiles_bin
export PATH
if [ -n "${BASH_VERSION:-}" ] && [ -r "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
fi
[ -r "$HOME/.profile.local" ] && . "$HOME/.profile.local"
:
