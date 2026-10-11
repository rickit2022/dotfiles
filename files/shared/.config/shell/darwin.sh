alias ls='ls -G'
if [ -z "${ANDROID_SDK_ROOT:-}" ] && [ -d "$HOME/Library/Android/sdk" ]; then
    ANDROID_SDK_ROOT="$HOME/Library/Android/sdk"
fi
studio() { open -a 'Android Studio' "$@"; }
