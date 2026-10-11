# POSIX syntax: sourced by both .bashrc and .zshrc.
[ -n "${DOTFILES_COMMON_LOADED:-}" ] && return
DOTFILES_COMMON_LOADED=1

dotfiles_path_prepend() {
    [ -d "$1" ] || return 0
    case ":$PATH:" in *":$1:"*) ;; *) PATH="$1:$PATH" ;; esac
    export PATH
}

case "$(uname -s)" in
    Darwin)
        if [ -x /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -x /usr/local/bin/brew ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        [ -r "$HOME/.config/shell/darwin.sh" ] && . "$HOME/.config/shell/darwin.sh"
        ;;
    Linux)
        [ -r "$HOME/.config/shell/linux.sh" ] && . "$HOME/.config/shell/linux.sh"
        ;;
esac

dotfiles_path_prepend "$HOME/bin"
dotfiles_path_prepend "$HOME/.local/bin"
dotfiles_path_prepend "$HOME/development/flutter/bin"
dotfiles_path_prepend /usr/local/go/bin
dotfiles_path_prepend "$HOME/go/bin"
if command -v nvim >/dev/null 2>&1; then
    export EDITOR="${EDITOR:-nvim}"
else
    export EDITOR="${EDITOR:-vi}"
fi

[ -r "$HOME/.bash_aliases" ] && . "$HOME/.bash_aliases"
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
dotfiles_path_prepend "$PYENV_ROOT/bin"
if command -v pyenv >/dev/null 2>&1; then
    case "${DOTFILES_SHELL:-}" in bash|zsh) eval "$(pyenv init - "$DOTFILES_SHELL")" ;; esac
fi

if [ -n "${ANDROID_SDK_ROOT:-}" ] && [ -d "$ANDROID_SDK_ROOT" ]; then
    export ANDROID_SDK_ROOT
    dotfiles_path_prepend "$ANDROID_SDK_ROOT/platform-tools"
    dotfiles_path_prepend "$ANDROID_SDK_ROOT/emulator"
fi
_dotfiles_emulator() {
    if [ -n "${ANDROID_SDK_ROOT:-}" ] && [ -x "$ANDROID_SDK_ROOT/emulator/emulator" ]; then
        printf '%s\n' "$ANDROID_SDK_ROOT/emulator/emulator"
    else
        command -v emulator
    fi
}
avd() {
    local emulator_bin avd_name
    emulator_bin=$(_dotfiles_emulator) || {
        printf '%s\n' 'Android emulator not found; set ANDROID_SDK_ROOT.' >&2; return 1;
    }
    avd_name=${1:-$("$emulator_bin" -list-avds 2>/dev/null | head -n 1)}
    [ -n "$avd_name" ] || {
        printf '%s\n' 'No AVD found; create one in Android Studio.' >&2; return 1;
    }
    case "$avd_name" in *[!A-Za-z0-9_.-]*) printf '%s\n' 'Invalid AVD name.' >&2; return 1 ;; esac
    nohup "$emulator_bin" -avd "$avd_name" >"${TMPDIR:-/tmp}/avd-$avd_name.log" 2>&1 &
    printf 'Launching AVD: %s\n' "$avd_name"
}

# Local settings and credentials stay outside Git.
[ -r "$HOME/.config/shell/local.sh" ] && . "$HOME/.config/shell/local.sh"
# Reuse the existing desktop/Keychain SSH agent instead of spawning one per shell.
export SDKMAN_DIR="${SDKMAN_DIR:-$HOME/.sdkman}"
[ -s "$SDKMAN_DIR/bin/sdkman-init.sh" ] && . "$SDKMAN_DIR/bin/sdkman-init.sh"
:
