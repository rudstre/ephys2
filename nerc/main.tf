
# Create an SSH keypair
resource "openstack_compute_keypair_v2" "ci_key" {
  name       = "ci_keypair"
  public_key = file("~/.ssh/nerc_ssh.pub")
}

# Create an Instance
resource "openstack_compute_instance_v2" "docserver" {
  name       = "ephys2-docserver"
  # Image Name of VM to start on NERC, look at the images in Horizon
  image_name = "ubuntu-20.04-x86_64"
  # VM Flavor: https://nerc-project.github.io/nerc-docs/openstack/create-and-connect-to-the-VM/flavors/
  # Availability depends upon your Quota i.e. vCPU / RAM / Disk, etc.
  flavor_name     = "cpu-a.2"
  key_pair        = openstack_compute_keypair_v2.ci_key.name
  security_groups = ["${openstack_networking_secgroup_v2.secgroup_1.name}"]

  network {
    name = "default_network"
  }
}

# Create Floating IP for each instance
resource "openstack_networking_floatingip_v2" "docserver_ip" {
  pool  = "provider"
}

# Assign a Floating IP
resource "openstack_compute_floatingip_associate_v2" "docserver_ip" {
  floating_ip = openstack_networking_floatingip_v2.docserver_ip.address
  instance_id = openstack_compute_instance_v2.docserver.id
}

# Create Security Group 
resource "openstack_networking_secgroup_v2" "secgroup_1" {
  name        = "ephys2-secgroup"
  description = "My security group"
}

# Add SSH Rule for Security Group 
resource "openstack_networking_secgroup_rule_v2" "ssh_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.secgroup_1.id
}

# Add HTTP Rule for Security Group 
resource "openstack_networking_secgroup_rule_v2" "http_ingress" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.secgroup_1.id
}

# Output variables
output "docserver_ip" {
  value = openstack_compute_floatingip_associate_v2.docserver_ip.floating_ip
}
