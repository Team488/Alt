# One-time setup for the Orange Pi's, needs to be connected to the internet

# Update and upgrade
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y docker.io
sudo apt-get install -y docker-compose-plugin

# Create udev rules for the color camera (ov9782)
echo 'ATTRS{idProduct}=="6366",ATTRS{idVendor}=="0c45",SYMLINK+="color_camera",GROUP="docker", MODE="0660"' | sudo tee /etc/udev/rules.d/99-usb-camera.rules

# Restart udev to apply changes
sudo systemctl restart udev

# Add docker group (if it doesn't already exist)
getent group docker || sudo groupadd docker

# Add user to docker group
sudo usermod -aG docker $USER

sudo newgrp docker
