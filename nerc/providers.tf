terraform {
  required_version = ">= 0.14.0"
  backend "swift" {
    container = "terraform-state"
    archive_container = "terraform-state-archive"
  }
  required_providers {
    openstack = {
      source = "terraform-provider-openstack/openstack"
    }
  }
}

provider "openstack" {
}