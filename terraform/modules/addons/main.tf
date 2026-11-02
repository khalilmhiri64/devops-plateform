locals {
  argo_repo = "https://argoproj.github.io/argo-helm"
}

resource "kubernetes_namespace_v1" "ns" {
  for_each = toset(["ingress-nginx", "argocd", "argo-rollouts", "monitoring", "vault", "gatekeeper-system"])
  metadata {
    name   = each.key
    labels = { "app.kubernetes.io/part-of" = "platform" }
  }
}

resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  namespace  = kubernetes_namespace_v1.ns["ingress-nginx"].metadata[0].name
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = "4.11.3"
  wait       = true
  values     = [file("${path.module}/values/ingress-nginx.yaml")]
}

resource "helm_release" "argocd" {
  name       = "argocd"
  namespace  = kubernetes_namespace_v1.ns["argocd"].metadata[0].name
  repository = local.argo_repo
  chart      = "argo-cd"
  version    = "7.7.11"
  values     = [file("${path.module}/values/argocd.yaml")]
  depends_on = [helm_release.ingress_nginx]
}

resource "helm_release" "argo_rollouts" {
  name       = "argo-rollouts"
  namespace  = kubernetes_namespace_v1.ns["argo-rollouts"].metadata[0].name
  repository = local.argo_repo
  chart      = "argo-rollouts"
  version    = "2.38.0"
  values     = [file("${path.module}/values/argo-rollouts.yaml")]
}

resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  namespace  = kubernetes_namespace_v1.ns["monitoring"].metadata[0].name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "66.3.1"
  timeout    = 900
  values = [
    templatefile("${path.module}/values/kube-prometheus-stack.yaml", {
      dashboard_json = jsonencode(jsondecode(file("${path.root}/../monitoring/grafana/dashboards/jobs-overview.json")))
      alert_rules    = indent(8, yamlencode(yamldecode(file("${path.root}/../monitoring/prometheus/alerts.yml")).groups))
    })
  ]
  set_sensitive {
    name  = "grafana.adminPassword"
    value = var.grafana_admin_password
  }
  depends_on = [helm_release.ingress_nginx]
}

resource "helm_release" "loki" {
  name       = "loki"
  namespace  = kubernetes_namespace_v1.ns["monitoring"].metadata[0].name
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki"
  version    = "6.24.0"
  values     = [file("${path.module}/values/loki.yaml")]
}

resource "helm_release" "promtail" {
  name       = "promtail"
  namespace  = kubernetes_namespace_v1.ns["monitoring"].metadata[0].name
  repository = "https://grafana.github.io/helm-charts"
  chart      = "promtail"
  version    = "6.16.6"
  values     = [file("${path.module}/values/promtail.yaml")]
  depends_on = [helm_release.loki]
}

resource "helm_release" "vault" {
  name       = "vault"
  namespace  = kubernetes_namespace_v1.ns["vault"].metadata[0].name
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  version    = "0.29.1"
  values     = [file("${path.module}/values/vault.yaml")]
  set_sensitive {
    name  = "server.dev.devRootToken"
    value = var.vault_root_token
  }
  depends_on = [helm_release.ingress_nginx]
}

resource "helm_release" "vault_secrets_operator" {
  name       = "vault-secrets-operator"
  namespace  = kubernetes_namespace_v1.ns["vault"].metadata[0].name
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault-secrets-operator"
  version    = "0.9.1"
  values     = [file("${path.module}/values/vault-secrets-operator.yaml")]
  depends_on = [helm_release.vault]
}

resource "helm_release" "gatekeeper" {
  name       = "gatekeeper"
  namespace  = kubernetes_namespace_v1.ns["gatekeeper-system"].metadata[0].name
  repository = "https://open-policy-agent.github.io/gatekeeper/charts"
  chart      = "gatekeeper"
  version    = "3.18.0"
  values     = [file("${path.module}/values/gatekeeper.yaml")]
}
