resource "kubernetes_namespace_v1" "this" {
  metadata {
    name = var.name
    labels = {
      "app.kubernetes.io/part-of"          = "jobs-platform"
      "jobs-platform/environment"          = var.environment
      "jobs-platform/managed"              = "true" # Gatekeeper constraints match on this
      "pod-security.kubernetes.io/enforce" = "restricted"
      "pod-security.kubernetes.io/warn"    = "restricted"
    }
  }
}

resource "kubernetes_resource_quota_v1" "this" {
  metadata {
    name      = "quota"
    namespace = kubernetes_namespace_v1.this.metadata[0].name
  }
  spec {
    hard = {
      "limits.cpu"             = var.cpu_quota
      "limits.memory"          = var.memory_quota
      "pods"                   = var.pod_quota
      "persistentvolumeclaims" = 5
      "services.loadbalancers" = 0
      "services.nodeports"     = 0
    }
  }
}

resource "kubernetes_limit_range_v1" "this" {
  metadata {
    name      = "defaults"
    namespace = kubernetes_namespace_v1.this.metadata[0].name
  }
  spec {
    limit {
      type            = "Container"
      default         = { cpu = "250m", memory = "256Mi" }
      default_request = { cpu = "50m", memory = "64Mi" }
    }
  }
}
