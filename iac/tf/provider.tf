terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }

    upcloud = {
      source  = "UpCloudLtd/upcloud"
      version = "~> 5.32"
    }
  }
}

provider "kubernetes" {
  client_certificate     = module.infra.cluster.client_certificate
  client_key             = module.infra.cluster.client_key
  cluster_ca_certificate = module.infra.cluster.cluster_ca_certificate
  host                   = module.infra.cluster.host

  ignore_annotations = [
    "^service\\.beta\\.kubernetes\\.io\\/.*load.*balancer.*"
  ]
}

provider "upcloud" {}
