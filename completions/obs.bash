# Bash completion for obs (Obsidian CLI Ops)
# Install: Source this file in your .bashrc or copy to /etc/bash_completion.d/

_obs_completion() {
    local cur prev words cword
    _init_completion || return

    local commands="check list sync install search audit r-dev help version"
    local r_dev_commands="link unlink status log context draft"
    local global_flags="-v --verbose"

    # Handle global flags
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "$global_flags" -- "$cur") )
        return 0
    fi

    # Complete main commands
    if [[ $cword -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "$commands $global_flags" -- "$cur") )
        return 0
    fi

    # Handle r-dev subcommands
    if [[ "${words[1]}" == "r-dev" ]]; then
        if [[ $cword -eq 2 ]]; then
            COMPREPLY=( $(compgen -W "$r_dev_commands" -- "$cur") )
            return 0
        fi

        case "${words[2]}" in
            log)
                if [[ $cword -eq 3 ]]; then
                    _filedir
                elif [[ "$prev" == "-m" ]]; then
                    # Waiting for message argument
                    return 0
                elif [[ $cword -eq 4 ]]; then
                    COMPREPLY=( $(compgen -W "-m" -- "$cur") )
                fi
                ;;
            draft|context)
                if [[ $cword -eq 3 ]]; then
                    _filedir
                fi
                ;;
            link)
                # Could suggest common paths, but leave open for user input
                return 0
                ;;
        esac
        return 0
    fi

    # Handle other command-specific completions
    case "${words[1]}" in
        install)
            if [[ $cword -eq 3 ]]; then
                COMPREPLY=( $(compgen -W "--all --vault" -- "$cur") )
            fi
            ;;
        sync)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "--force" -- "$cur") )
            fi
            ;;
    esac
}

complete -F _obs_completion obs
