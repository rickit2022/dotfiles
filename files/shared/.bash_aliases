# Aliases shared by Bash and Zsh.
alias dotfiles='dotfiles-sync'
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias emu='avd'
if [ -x "$HOME/scripts/.start.sh" ] && [ "$(uname -s)" = Linux ]; then
    alias qwe="$HOME/scripts/.start.sh"
fi
