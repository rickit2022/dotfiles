# Zsh has its own history, prompt and completion settings.
[[ -o interactive ]] || return
HISTFILE="$HOME/.zsh_history"
HISTSIZE=1000
SAVEHIST=2000
setopt APPEND_HISTORY HIST_IGNORE_DUPS HIST_IGNORE_SPACE
PROMPT='%F{green}%n@%m%f:%F{blue}%~%f%# '
DOTFILES_SHELL=zsh
[[ -r "$HOME/.config/shell/common.sh" ]] && . "$HOME/.config/shell/common.sh"
autoload -Uz compinit
compinit
[[ -r "$HOME/.zshrc.local" ]] && . "$HOME/.zshrc.local"
:
