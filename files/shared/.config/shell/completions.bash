# Native completion; candidates never run the commands or probe account quotas.
_dotfiles_cli_complete() {
    local kind="$1" cur prev command='' commands global options word path i
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}
    COMPREPLY=()
    if type compopt >/dev/null 2>&1; then
        compopt +o filenames 2>/dev/null || :
    fi
    case "$kind" in
        dotfiles)
            commands='status capture apply audit sync'
            global='--home'
            ;;
        recovery)
            commands='on off attach list accounts status run check'
            global='--config'
            ;;
    esac
    if [ "$prev" = '=' ] && [ "${COMP_WORDS[COMP_CWORD-2]}" = "$global" ]; then
        prev=$global
    fi

    # A global option's value may itself look like a subcommand.
    for ((i=1; i<COMP_CWORD; i++)); do
        word=${COMP_WORDS[i]}
        case "$word" in
            "$global")
                ((i++))
                [ "${COMP_WORDS[i]}" = '=' ] && ((i++))
                ;;
            "$global"=*|-*) ;;
            *) command=$word; break ;;
        esac
    done

    if [ "$prev" = "$global" ]; then
        if type compopt >/dev/null 2>&1; then
            compopt -o filenames 2>/dev/null || :
        fi
        options='-f'
        [ "$kind" = dotfiles ] && options='-d'
        while IFS= read -r path; do
            [ -d "$path" ] && path="$path/"
            COMPREPLY+=("$path")
        done < <(compgen "$options" -- "$cur")
        return 0
    fi
    if [ "$kind" = dotfiles ] && [ "$command" = sync ]; then
        case "$prev" in -m|--message) return 0 ;; esac
    fi

    options='-h --help'
    if [ -z "$command" ]; then
        options="$commands $global $options"
    else
        case "$kind:$command" in
            dotfiles:capture|dotfiles:apply|recovery:check) options="$options --dry-run" ;;
            dotfiles:sync) options="$options --dry-run -m --message" ;;
            recovery:run) options="$options --dry-run --json" ;;
            recovery:status) options="$options --json" ;;
            dotfiles:status|dotfiles:audit|recovery:on|recovery:off|recovery:attach|recovery:list|recovery:accounts) ;;
            *) return 0 ;;
        esac
    fi
    COMPREPLY=( $(compgen -W "$options" -- "$cur") )
    return 0
}

_dotfiles_sync_complete() { _dotfiles_cli_complete dotfiles; }
_codex_recovery_complete() { _dotfiles_cli_complete recovery; }
complete -o filenames -F _dotfiles_sync_complete dotfiles-sync dotfiles
complete -o filenames -F _codex_recovery_complete codex-recovery
