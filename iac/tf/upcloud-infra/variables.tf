variable "prefix" {
  type    = string
  default = "photo-objects-"
}

variable "cidr" {
  type    = string
  default = "172.24.16.0/24"
}

variable "zone" {
  type    = string
  default = "fi-hel2"
}

variable "region" {
  type    = string
  default = "europe-1"
}

// For service annotations
variable "lb_plan" {
  type    = string
  default = "essentials"
}

variable "url" {
  type    = string
  default = ""
}
