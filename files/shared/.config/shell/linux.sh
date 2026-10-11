unset GTK_MODULES
if command -v dircolors >/dev/null 2>&1; then
    eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
fi
if [ -z "${ANDROID_SDK_ROOT:-}" ] && [ -d "$HOME/Android/Sdk" ]; then
    ANDROID_SDK_ROOT="$HOME/Android/Sdk"
fi
if [ -x "$HOME/android-studio/bin/studio.sh" ]; then
    alias studio='"$HOME/android-studio/bin/studio.sh"'
fi
