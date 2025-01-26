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

		  # -------------- nginx install from nginx repo
		  sudo apt install curl gnupg2 ca-certificates lsb-release ubuntu-keyring
		  curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor \
					 | sudo tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null
		  out=$(gpg --dry-run --quiet --no-keyring --import --import-options import-show /usr/share/keyrings/nginx-archive-keyring.gpg)
		  fingerprints=(
					 "8540A6F18833A80E9C1653A42FD21310B49F6B46" 
					 "573BFD6B3D8FBC641079A6ABABF5BD827BD9BF62" 
					 "9E9BE90EACBCDE69FE9B204CBCDCD8A38D88A2B3"
		  )
		  for fingerprint in "${fingerprints[@]}"; do
					 if [[ ! $out == *"$fingerprint"* ]];then
								echo "Mismatched fingerprints. Please retry download."
								break
					 fi
		  done
		  echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
					 http://nginx.org/packages/ubuntu `lsb_release -cs` nginx" \
					 | sudo tee /etc/apt/sources.list.d/nginx.list
		  echo -e "Package: *\nPin: origin nginx.org\nPin: release o=nginx\nPin-Priority: 900\n" \
					 | sudo tee /etc/apt/preferences.d/99nginx
		  sudo apt update
		  sudo apt install nginx
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
