locals {
  real_ip_config = var.real_ip_from == "" ? "" : <<-EOT
  set_real_ip_from ${var.real_ip_from};
  real_ip_header X-Forwarded-For;
  EOT
}
