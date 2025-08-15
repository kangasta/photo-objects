terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

locals {
  lb_url = "https://${kubernetes_service.ui.status[0].load_balancer[0].ingress[0].hostname}"
}


resource "kubernetes_namespace" "this" {
  metadata {
    name = var.namespace
  }
}

resource "random_password" "db" {
  length  = 16
  special = false
}

resource "kubernetes_secret" "api" {
  metadata {
    name      = "api"
    namespace = var.namespace
  }

  data = {
    db_connect_url    = var.db_connect_url != "" ? var.db_connect_url : "postgresql://django:${random_password.db.result}@db:5432/django"
    objsto_access_key = var.objsto_access_key
    objsto_secret_key = var.objsto_secret_key
  }
}

resource "kubernetes_deployment" "api" {
  metadata {
    name      = "api"
    namespace = var.namespace
    labels = {
      app = "api"
    }
  }

  spec {
    selector {
      match_labels = {
        app = "api"
      }
    }

    template {
      metadata {
        labels = {
          app = "api"
        }
      }

      spec {
        container {
          image = "ghcr.io/kangasta/photo-objects-api:${var.app_version}"
          name  = "api"

          env {
            name = "DB_URL"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.api.metadata[0].name
                key  = "db_connect_url"
              }
            }
          }

          env {
            name = "OBJSTO_ACCESS_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.api.metadata[0].name
                key  = "objsto_access_key"
              }
            }
          }

          env {
            name = "OBJSTO_SECRET_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.api.metadata[0].name
                key  = "objsto_secret_key"
              }
            }
          }

          env {
            name  = "OBJSTO_HOST"
            value = var.objsto_host
          }

          env {
            name  = "URL"
            value = var.url != "" ? var.url : local.lb_url
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "api" {
  metadata {
    name      = "api"
    namespace = var.namespace
  }
  spec {
    selector = {
      app = "api"
    }

    port {
      port        = 8000
      target_port = 8000
    }

    type = "ClusterIP"
  }
}

resource "kubernetes_config_map" "ui" {
  metadata {
    name      = "ui"
    namespace = var.namespace
  }
  data = {
    resolver = "resolver ${var.dns_service}.kube-system.svc.cluster.local;"
  }
  depends_on = [kubernetes_service.api]
}

resource "kubernetes_deployment" "ui" {
  metadata {
    name      = "ui"
    namespace = var.namespace
    labels = {
      app = "ui"
    }
  }

  spec {
    selector {
      match_labels = {
        app = "ui"
      }
    }

    template {
      metadata {
        labels = {
          app = "ui"
        }
      }

      spec {
        container {
          image = "ghcr.io/kangasta/photo-objects-front:${var.app_version}"
          name  = "ui"

          env {
            name  = "OBJSTO_HOST"
            value = var.objsto_host
          }

          env {
            name  = "OBJSTO_PORT"
            value = "443"
          }

          env {
            name  = "OBJSTO_PROTOCOL"
            value = "https"
          }

          volume_mount {
            name       = "ui"
            mount_path = "/etc/nginx/conf.d/resolver.conf"
            sub_path   = "resolver"
          }
        }

        volume {
          name = "ui"
          config_map {
            name = "ui"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "ui" {
  metadata {
    name        = "ui"
    namespace   = var.namespace
    annotations = var.ui_service_annotations
  }

  spec {
    selector = {
      app = "ui"
    }

    port {
      port        = 443
      target_port = 80
    }

    type = "LoadBalancer"
  }
}

resource "kubernetes_persistent_volume_claim" "db" {
  count = var.pvc_storage_class != "" ? 1 : 0

  metadata {
    name      = "db"
    namespace = var.namespace
  }

  spec {
    storage_class_name = var.pvc_storage_class
    access_modes       = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}

resource "kubernetes_secret" "db" {
  metadata {
    name      = "db"
    namespace = var.namespace
  }

  data = {
    password = random_password.db.result
  }
}


resource "kubernetes_deployment" "db" {
  count = var.db_connect_url != "" ? 0 : 1

  metadata {
    name      = "db"
    namespace = var.namespace
    labels = {
      app = "db"
    }
  }

  spec {
    selector {
      match_labels = {
        app = "db"
      }
    }

    template {
      metadata {
        labels = {
          app = "db"
        }
      }

      spec {
        container {
          image = "postgres:14"
          name  = "db"

          env {
            name  = "POSTGRES_USER"
            value = "django"
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db.metadata[0].name
                key  = "password"
              }
            }
          }

          env {
            name  = "POSTGRES_DB"
            value = "django"
          }

          env {
            name  = "PGDATA"
            value = "/var/lib/postgresql/data/pgdata"
          }

          dynamic "volume_mount" {
            for_each = kubernetes_persistent_volume_claim.db
            content {
              name       = "db-datadir"
              mount_path = "/var/lib/postgresql/data"
            }
          }
        }

        dynamic "volume" {
          for_each = kubernetes_persistent_volume_claim.db
          content {
            name = "db-datadir"
            persistent_volume_claim {
              claim_name = volume.value.metadata[0].name
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "db" {
  count = var.db_connect_url != "" ? 0 : 1

  metadata {
    name      = "db"
    namespace = var.namespace
  }
  spec {
    selector = {
      app = "db"
    }

    port {
      port        = 5432
      target_port = 5432
    }
  }
}