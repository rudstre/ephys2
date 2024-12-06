#!/bin/bash

# Exit when any command fails
set -e

# Ensure SSH key is available
if [ -z "$NERC_SSH_KEY" ]; then
	echo "Please set NERC_SSH_KEY. Exiting."
	exit 1
fi

# Get IP address of docserver
NERC_DOCS_IP=$(terraform output docserver_ip | tr -d '"')

# Ensure correct directory
if [ ! -f "main.tf" ]; then
	echo "Please run this script from the nerc/ directory. Exiting."
	exit 1
fi

# Copy static files
ssh -i $NERC_SSH_KEY "ubuntu@$NERC_DOCS_IP" "rm -rf ~/docserver"
scp -i $NERC_SSH_KEY -r ../docs/_build/html "ubuntu@$NERC_DOCS_IP:~/docserver" 

# Connect and provision nginx
ssh -i $NERC_SSH_KEY "ubuntu@$NERC_DOCS_IP" /bin/bash << EOF
sudo su

# Install nginx
apt-get update
apt-get -y install nginx

# Start the service
systemctl start nginx
EOF

# Copy nginx configuration 
scp -i $NERC_SSH_KEY docserver.conf "ubuntu@$NERC_DOCS_IP:~/docserver.conf" 

# Connect and reload nginx
ssh -i $NERC_SSH_KEY "ubuntu@$NERC_DOCS_IP" /bin/bash << EOF
sudo su
chmod -R u+rx /home/ubuntu/docserver
rm -f /etc/nginx/sites-enabled/default
rm -rf /var/cache/nginx
ln -sf /home/ubuntu/docserver.conf /etc/nginx/sites-available/
ln -sf /home/ubuntu/docserver.conf /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
EOF

echo "Docserver started at $NERC_DOCS_IP"