provider "kubernetes" {
  config_path    = var.kubeconfig_path
  config_context = var.kube_context
}

provider "helm" {
  kubernetes {
    config_path    = var.kubeconfig_path
    config_context = var.kube_context
  }
}

# Vault runs inside the cluster (dev mode) and is reached through the ingress.
# Because of that, apply in two phases: see scripts/bootstrap.sh.
provider "vault" {
  address          = var.vault_address
  token            = var.vault_root_token
  skip_child_token = true
}
