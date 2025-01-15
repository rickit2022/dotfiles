#!/bin/bash

_start(){
		  local cur prev opts 
		  COMPREPLY=()
		  cur="${COMP_WORDS[COMP_CWORD]}"
		  prev="${COMP_WORDS[COMP_CWORD - 1]}"
		  commands_opts="--connect --ssh --firefox --help"
		  connect_opts="wifi server"

		  # $3 being the word 'before' the word being completed
		  if [[ "$prev" == "--connect" || "$prev" == "-c" ]]; then 
					 COMPREPLY=( $(compgen -W "$connect_opts" -- "$cur") )
		  else
					 COMPREPLY=( $(compgen -W "$commands_opts" -- "$cur") )
		  fi	
}

complete -F _start qwe
