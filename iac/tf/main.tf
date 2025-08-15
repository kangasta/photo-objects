module "infra" {
    source = "./upcloud-infra"
}

module "app" {
  source = "./kubernetes-app"

  app_version = var.app_version
  url = var.url

  pvc_storage_class = "upcloud-block-storage-maxiops"

  objsto_host = module.infra.objsto.host
  objsto_access_key = module.infra.objsto.access_key
  objsto_secret_key = module.infra.objsto.secret_key

  ui_service_annotations = {
    "service.beta.kubernetes.io/upcloud-load-balancer-config" = jsonencode({
        plan = "essentials",
    })
  }
}
