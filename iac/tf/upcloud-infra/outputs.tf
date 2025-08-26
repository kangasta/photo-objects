output "cluster" {
  value = data.upcloud_kubernetes_cluster.this
}

output "objsto" {
  value = {
    access_key = upcloud_managed_object_storage_user_access_key.django.access_key_id
    secret_key = upcloud_managed_object_storage_user_access_key.django.secret_access_key
    host       = tolist(upcloud_managed_object_storage.this.endpoint)[0].domain_name
  }
}

locals {
  rules = var.url == "" ? [] : [
    {
      name     = "reject-invalid-host"
      priority = 100
      matchers = [
        {
          type    = "host"
          inverse = true
          match_host = {
            value = var.url
          }
        }
      ]
      actions = [
        {
          type              = "tcp_reject"
          action_tcp_reject = {}
        }
      ]
    }
  ]
}

output "service_annotations" {
  value = {
    "service.beta.kubernetes.io/upcloud-load-balancer-config" = jsonencode({
      plan = var.lb_plan
      frontends = [
        {
          rules = local.rules
        }
      ]
    })
  }
}
