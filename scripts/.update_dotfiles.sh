#!/bin/bash
if ! alias dotfiles >/dev/null 2>&1; then
	echo "Setting 'dotfiles' alias..."
	echo "alias dotfiles='git --git-dir=$HOME/dotfiles --work-tree=$HOME'" >> "$HOME/.bash_aliases"
	source $HOME/.bash_aliases
	echo "source /usr/share/bash-completion/completions/git" >> $HOME/.bashrc
	echo "__git_complete dotfiles __git_main" >> $HOME/.bashrc
	source $HOME/.bashrc
	dotfiles config --global core.editor "vim"
fi

echo "Checking git configs..."
username=$(git config --global user.name)

if [[ -z "$username"  ]]; then
	echo "Username not found, would you like to set your configs? (y/n)"
	read -r pr
	if [[ $pr == 'y' ]];then
		echo "Enter your username:"
		read -r pr
		username=$pr
		git config --global user.name "$username"

		echo "Username set to $username"
	fi
fi


backup(){	
	echo "backing up..."
	mkdir -p $HOME/.dotfiles_backup	
}

push_updates(){
	echo "pushing changes..."
	dotfiles remote set-url origin "git@github.com:$username/dotfiles" > /dev/null 2>&1
	if [ ! $? -eq 0 ]; then
		  dotfiles remote add origin "git@github.com:$username/dotfiles"
	fi
	dotfiles fetch origin # not merging changes(git pull) since there could be conflict(s)
	dotfiles push origin main
}

track_filelist(){
   echo "tracking files..."
   while read -r line; do 
	if [[ -d $line ]]; then 
			 cd $line && dotfiles add . && cd "$HOME"
	fi

	dotfiles add $line
	echo "added $line"; 
   done < "$HOME/.filelist"
}

init(){
	echo "pulling changes..." 
	git clone --git-dir=$HOME/dotfiles --bare "https://github.com/$username/dotfiles"
   dotfiles config --local status.showUntrackedFiles no
	cd $HOME && dotfiles checkout
	if ! $? -eq 0; then 
			  echo "conflicts detected! Run backup() to save files"
		backup	
	fi
	dotfiles checkout
}

OPT=$(getopt -o "bpti" --long "backup,push,track,init" -- "$@" )
eval set -- "$OPT"

while [ $# -gt 0 ]; do
		  case "$1" in 
		  -b|--backup)
					 backup
					 shift
					 ;;
		  -p|--pushupdates)
					 push_updates
					 shift
					 ;;
		  -t|--track_filelist)
					 track_filelist
					 shift
					 ;;
		  -i|--init)
					 init
					 shift
					 ;;
			--)
					exit 0
					;;
		  *)
					 echo "invalid args: $1"
					 exit 1
					 ;;
		  esac
					 shift
done
