# Bash login shells (including macOS) must also load the interactive setup.
[ -r "$HOME/.profile" ] && . "$HOME/.profile"
:
