locals {
  app_namespaces = { for env, cfg in var.environments : env => merge(cfg, { name = "jobs-${env}" }) }
}

# Cluster add-ons: ingress, GitOps, progressive delivery, observability, security.
module "addons" {
  source                 = "./modules/addons"
  vault_root_token       = var.vault_root_token
  grafana_admin_password = var.grafana_admin_password
}

# Application namespaces with quotas, default limits and Pod Security labels.
module "namespaces" {
  source   = "./modules/namespace"
  for_each = local.app_namespaces

  name         = each.value.name
  environment  = each.key
  cpu_quota    = each.value.cpu_quota
  memory_quota = each.value.memory_quota
  pod_quota    = each.value.pod_quota
}

# Secrets, policies and Kubernetes auth in Vault.
module "vault_config" {
  source = "./modules/vault-config"
  count  = var.enable_vault_config ? 1 : 0

  namespaces = [for ns in local.app_namespaces : ns.name]
  policy_dir = "${path.root}/../security/vault/policies"

  depends_on = [module.addons, module.namespaces]
}

# ArgoCD project + applications (app definitions live in argocd/).
resource "helm_release" "argocd_apps" {
  name       = "argocd-apps"
  namespace  = module.addons.argocd_namespace
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argocd-apps"
  version    = "2.0.2"

  values = [templatefile("${path.root}/../argocd/applications.yaml.tftpl", {
    repo_url = var.gitops_repo_url
    revision = var.gitops_revision
  })]

  depends_on = [module.addons, module.namespaces]
}
