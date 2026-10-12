# Load after compinit. Completion uses shell metadata, never live CLI queries.
_dotfiles_sync() {
    local context state state_descr line
    typeset -A opt_args
    local -a commands
    commands=(
        'status:Show configuration differences and Git status'
        'capture:Copy selected live configurations into the repository'
        'apply:Install saved configurations with backups'
        'audit:Check publishable files for credentials'
        'sync:Capture, check, commit and push selected configurations'
    )
    _arguments -C \
        '(-h --help)'{-h,--help}'[Show help]' \
        '--home[Use another home directory]:home directory:_directories' \
        '1:command:->commands' \
        '*::argument:->arguments'
    case "$state" in
        commands) _describe 'command' commands ;;
        arguments)
            case "$line[1]" in
                capture|apply)
                    _arguments '(-h --help)'{-h,--help}'[Show help]' \
                        '--dry-run[Preview without changing files]'
                    ;;
                sync)
                    _arguments '(-h --help)'{-h,--help}'[Show help]' \
                        '--dry-run[Preview without commit, fetch or push]' \
                        '(-m --message)'{-m,--message}'[Set the commit message]:message:'
                    ;;
                status|audit) _arguments '(-h --help)'{-h,--help}'[Show help]' ;;
            esac
            ;;
    esac
}

_codex_recovery() {
    local context state state_descr line
    typeset -A opt_args
    local -a commands
    commands=(
        'on:Enable automatic recovery and select a conversation'
        'off:Disable automatic recovery'
        'attach:Attach to the recovery conversation in tmux'
        'list:List conversations with goals'
        'accounts:Choose accounts for rotation'
        'status:Show recovery status'
        'run:Resume the selected goal now'
        'check:Run an automatic recovery check'
    )
    _arguments -C \
        '(-h --help)'{-h,--help}'[Show help]' \
        '--config[Use another recovery configuration]:configuration file:_files' \
        '1:command:->commands' \
        '*::argument:->arguments'
    case "$state" in
        commands) _describe 'command' commands ;;
        arguments)
            case "$line[1]" in
                run)
                    _arguments '(-h --help)'{-h,--help}'[Show help]' \
                        '--dry-run[Preview account selection without resuming]' \
                        '--json[Print JSON events and result]'
                    ;;
                check)
                    _arguments '(-h --help)'{-h,--help}'[Show help]' \
                        '--dry-run[Probe quotas without resuming]'
                    ;;
                status)
                    _arguments '(-h --help)'{-h,--help}'[Show help]' \
                        '--json[Print JSON status]'
                    ;;
                on)
                    _arguments '(-h --help)'{-h,--help}'[Show help]' \
                        '1:conversation ID:'
                    ;;
                off|attach|list|accounts) _arguments '(-h --help)'{-h,--help}'[Show help]' ;;
            esac
            ;;
    esac
}

compdef _dotfiles_sync dotfiles-sync dotfiles
compdef _codex_recovery codex-recovery
