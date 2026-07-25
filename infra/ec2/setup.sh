#!/bin/bash
set -e

sudo apt update && sudo apt upgrade -y

sudo apt install -y ca-certificates curl gnupg

#Docker and that
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

#Install Docker Engineer and Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable docker
sudo systemctl start docker

#adding ubuntu user to docker group
sudo usermod -aG docker ubuntu

#make app directry 
mkdir -p /home/ubuntu/app

echo "Bootstrap done. Log out and in again "