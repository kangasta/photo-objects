locals {
  # Parse hostname from URL for certificate and invalid host rule
  hostname = var.url == "" ? "" : regex("https{0,1}://(?<hostname>[^/]+)", var.url).hostname
  # Rules for the service annotations
  rules = concat(
    [{
      name     = "set-forwarded-headers"
      priority = 90
      actions = [
        {
          type                         = "set_forwarded_headers"
          action_set_forwarded_headers = {}
        }
      ]
    }],
    local.hostname == "" ? [] : [
      {
        name     = "reject-invalid-host"
        priority = 100
        matchers = [
          {
            type    = "host"
            inverse = true
            match_host = {
              value = local.hostname
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
  ])
  # TLS configurations for the service annotations
  tls_configs = length(upcloud_loadbalancer_dynamic_certificate_bundle.this) == 0 ? [
    { name = "needs-certificate" }
    ] : [
    for i in upcloud_loadbalancer_dynamic_certificate_bundle.this : {
      certificate_bundle_uuid = i.id
      name                    = i.name
    }
  ]
}
