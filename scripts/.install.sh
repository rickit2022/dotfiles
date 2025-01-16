#!/bin/bash

full(){
   if grep -q "Ubuntu" /etc/*release; then
		  sudo apt update 
		  sudo apt -y install vim neovim 

		  # -------------- docker install
		  sudo apt-get -y purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras

		  sudo apt-get update
		  sudo apt-get -y install ca-certificates curl
		  sudo install -m 0755 -d /etc/apt/keyrings
		  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
		  sudo chmod a+r /etc/apt/keyrings/docker.asc

		  # Add the docker repository to Apt sources:
		  echo \
		  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
		  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
		  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
		  sudo apt-get update

		  sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

		  # -------------- custom fonts install
		  mkdir -p ~/.local/share/fonts
		  cp ~/fonts ~/.local/share/fonts
		  if ! fc-cache >/dev/null 2>&1; then sudo apt -y install fontconfig; fi
		  fc-cache -f -v
		  echo -e "Installed fonts:\n$(fc-list | grep .local/share/fonts)"

		  # -------------- ssh setup
   fi
}

compact(){
		  apt -y install vim 
}

if [[ $# -eq 0 || ($# -eq 1 && ("$1" == "full" || "$1" == 'f')) ]]; then 
		  full
		  exit 0
elif [[ $# -eq 1 && ("$1" == "compact" || "$1" == 'c') ]]; then 
		  compact 
		  exit 0
else
		  echo "Bad args: Failed to parse options"
fi
