#!/bin/bash
greet() { echo "Hello world!"; }
warn() { echo; echo "type -h | --help to see available options"; }
usage() {
		  echo
		  echo "A script for running some common tasks"
		  echo "Usage: $0 <args> || qwe <args>"; 
		  echo 
		  echo "Args:"
		  echo
		  echo "-s, --ssh	Start an ssh-agent session"
		  echo "-f, --firefox	opens firefox"	
		  echo "-c, --conect	wifi | server | etc"
		  echo "-h, --help	Display help information"
		  echo
		  echo "To view errors, navigate ~/.startError.log"
		  echo
}

OPT=$(getopt -o "hscf" --long "help,ssh,connect,firefox" -- "$@" )
eval set -- "$OPT"

if [ $? -ne 0 ]; then
	echo "Bad args: Failed to parse options"
	exit 1
fi

if [ $# -eq 1 ]; then 
	greet
	eval $(ssh-agent -s) &
	firefox &
	gnome-terminal -- bash -c "tmux; exec bash" &
	exit 0
fi
while [[ $# -gt 0 ]]; do 
		  case "$1" in
		  -h|--help)
			usage
			;;
		  -s|--ssh)
			eval $(ssh-agent -s)
			;;
		  -f|--firefox)
					 if [[ -n "$3" ]]; then
								echo
								echo "Opening $3 in the browser..."
								echo
								 firefox --new-tab "$3" > /dev/null 2>&1 
					 else
								 firefox > /dev/null 2>&1 
					 fi
			;;
		  -c|--connect)
			shift
			if [ -n "$2" ]; then
				case "$2" in
					wifi)
						SSIDs=$(nmcli -f BSSID,SSID,CHAN,SIGNAL dev wifi list | tail --lines=+2 | head --lines=10 | sort -k2 | nl)
						echo "$SSIDs"
						echo
						read -p "Select an SSID(1-10)[leave blank for strongest signal]: " pr
						if [ ${#pr} -eq 0 ]; then
							BSSID=$(echo "$SSIDs" | tr -s ' ' | cut -d'	' -f2 | cut -d' ' -f1 | tail -n1)		
							SSID=$(nmcli device wifi list | grep "$BSSID" | awk '{print $2}')
						else
						# dbus-send --system --print-reply --dest=org.freedesktop.systemd1 /org/freedesktop/systemd1   org.freedesktop.DBus.Introspectable.Introspect
							BSSID=$(echo "$SSIDs" | cut -d '	' -f2 | cut -d ' ' -f1 | tail --lines=+$pr | head --lines=1 | tr '\:' ':')
							SSID=$(nmcli device wifi list | grep "$BSSID" | awk '{print $2}')

						fi
						echo connecting to "$SSID..."
						nmcli dev wifi connect "$BSSID"
						;;
					server)
						echo "connecting to server..."
						;;
					*)
						echo "connect: $2 is not a valid argument"
						warn
						exit 1
						;;	
				esac	
				shift
			else
				echo "connect: $1 not recognised"
			fi 
					  ;;
		  --)
					 if [ -n "$2" ]; then
								case "$2" in
										  tbf)
													 cur_window=$(tmux display-message -p '#I')
													 tmux new-window -n "Ang/todo" "cd ~/Projects/Ang/todo && ng serve"
													 tmux select-window -t "$cur_window"
													 sleep 4 && ~/.start.sh -f localhost:4200;
													 ;;
										  *)
													 # only if user provides an unrecognised string with no previous commands, output error
													 if [[ -z "$prev_command" ]]; then
																warn
																exit 1;
													 fi
													 ;;
								esac
								shift
					 fi 
					 shift
					  ;;
		  *)
					  echo "Unexpected option: $1"
					  exit 1
					  ;;
		  esac
					 shift
					 prev_command="$1"
done

if [[ $# -gt 0 ]]; then
	LOG_FILE=~/.startError.log
	if [ ! -f "$LOG_FILE" ]; then
		touch "$LOG_FILE"
	fi
	while [[ $# -gt 0 ]]; do
		echo "unused positional arguments: $1" >> "$LOG_FILE" 2>&1
		shift
	done
fi

