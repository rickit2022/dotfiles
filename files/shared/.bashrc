# Interactive Bash setup; shared settings also work with Zsh on macOS.
case $- in *i*) ;; *) return ;; esac
HISTCONTROL=ignoreboth
HISTSIZE=1000
HISTFILESIZE=2000
shopt -s histappend checkwinsize
PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
DOTFILES_SHELL=bash
[ -r "$HOME/.config/shell/common.sh" ] && . "$HOME/.config/shell/common.sh"
if [ -r /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
elif [ -r /etc/bash_completion ]; then
    . /etc/bash_completion
fi
if [ -r "${NVM_DIR:-$HOME/.nvm}/bash_completion" ]; then
    . "${NVM_DIR:-$HOME/.nvm}/bash_completion"
fi
_avd_complete() {
    local emulator_bin
    emulator_bin=$(_dotfiles_emulator) || return
    COMPREPLY=( $(compgen -W "$("$emulator_bin" -list-avds 2>/dev/null)" -- "${COMP_WORDS[COMP_CWORD]}") )
}
complete -F _avd_complete avd
[ -r "$HOME/.bashrc.local" ] && . "$HOME/.bashrc.local"
:
