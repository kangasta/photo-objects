terraform {
  required_providers {
    upcloud = {
      source = "UpCloudLtd/upcloud"
      version = "~> 5.24"
    }
  }
}

resource "upcloud_router" "this" {
  name = "${var.prefix}router"
}

resource "upcloud_gateway" "this" {
  name     = "${var.prefix}gw"
  plan     = "essentials"
  zone     = var.zone
  features = ["nat"]

  router {
    id = upcloud_router.this.id
  }
}

resource "upcloud_network" "this" {
  name = "${var.prefix}net"
  zone = var.zone
  ip_network {
    address            = var.cidr
    dhcp               = true
    family             = "IPv4"
    dhcp_default_route = true
  }
  router = upcloud_router.this.id
}

resource "upcloud_kubernetes_cluster" "this" {
  control_plane_ip_filter = ["0.0.0.0/0"]
  name                    = "${var.prefix}cluster"
  network                 = upcloud_network.this.id
  zone                    = var.zone
  plan                    = "dev-md"
  private_node_groups     = true
}

data "upcloud_kubernetes_cluster" "this" {
  id = upcloud_kubernetes_cluster.this.id
}

resource "upcloud_kubernetes_node_group" "default" {
  cluster    = upcloud_kubernetes_cluster.this.id
  node_count = 1
  name       = "default"
  plan       = "2xCPU-4GB"
}

resource "upcloud_managed_object_storage" "this" {
  name              = "${var.prefix}objsto"
  region            = var.region
  configured_status = "started"

  network {
    family = "IPv4"
    name   = "private-IPv4"
    type   = "private"
    uuid   = upcloud_network.this.id
  }
}

resource "upcloud_managed_object_storage_user" "django" {
  username     = "django"
  service_uuid = upcloud_managed_object_storage.this.id
}

resource "upcloud_managed_object_storage_user_access_key" "django" {
  username     = upcloud_managed_object_storage_user.django.username
  service_uuid = upcloud_managed_object_storage.this.id
  status       = "Active"
}

resource "upcloud_managed_object_storage_policy" "full_access" {
  name        = "FullAccess"
  description = "Allow full access to all S3 resources."
  document = urlencode(jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:*"
        Resource = "*"
      }
    ]
  }))
  service_uuid = upcloud_managed_object_storage.this.id
}

resource "upcloud_managed_object_storage_user_policy" "django_full_access" {
  name         = upcloud_managed_object_storage_policy.full_access.name
  username     = upcloud_managed_object_storage_user.django.username
  service_uuid = upcloud_managed_object_storage.this.id
}
