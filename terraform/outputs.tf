output "urls" {
  description = "Entry points (all resolve to 127.0.0.1 via localtest.me)."
  value = {
    staging    = "http://staging.jobs.localtest.me"
    production = "http://jobs.localtest.me"
    preview    = "http://preview.jobs.localtest.me"
    argocd     = "http://argocd.localtest.me"
    grafana    = "http://grafana.localtest.me"
    prometheus = "http://prometheus.localtest.me"
    vault      = "http://vault.localtest.me"
  }
}

output "namespaces" {
  value = [for ns in module.namespaces : ns.name]
}

output "argocd_admin_password_cmd" {
  value = "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
}
