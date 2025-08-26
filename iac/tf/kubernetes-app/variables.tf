variable "url" {
  type    = string
  default = ""
}

variable "namespace" {
  type    = string
  default = "photo-objects"
}

variable "dns_service" {
  type    = string
  default = "coredns"
}

variable "pvc_storage_class" {
  type    = string
  default = ""
}

variable "db_connect_url" {
  type      = string
  default   = ""
  sensitive = true
}

variable "app_version" {
  type    = string
  default = "latest"
}

variable "objsto_host" {
  type    = string
  default = ""
}

variable "objsto_access_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "objsto_secret_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "ui_service_annotations" {
  type    = map(string)
  default = {}
}

variable "real_ip_from" {
  type    = string
  default = ""
}
