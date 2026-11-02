variable "kubeconfig_path" {
  description = "Path to the kubeconfig file."
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "kubectl context to deploy into. Docker Desktop names it docker-desktop."
  type        = string
  default     = "docker-desktop"
}

variable "environments" {
  description = "Application environments and their resource quotas."
  type = map(object({
    cpu_quota    = string
    memory_quota = string
    pod_quota    = number
  }))
  default = {
    staging    = { cpu_quota = "4", memory_quota = "4Gi", pod_quota = 30 }
    production = { cpu_quota = "8", memory_quota = "8Gi", pod_quota = 60 }
  }
}

variable "gitops_repo_url" {
  description = "Git repository that ArgoCD watches."
  type        = string
}

variable "gitops_revision" {
  description = "Branch ArgoCD tracks."
  type        = string
  default     = "main"
}

variable "vault_address" {
  description = "Vault URL as seen from the machine running Terraform."
  type        = string
  default     = "http://vault.localtest.me"
}

variable "vault_root_token" {
  description = "Vault dev-mode root token. Local use only."
  type        = string
  sensitive   = true
  default     = "root-local-only"
}

variable "grafana_admin_password" {
  description = "Grafana admin password."
  type        = string
  sensitive   = true
  default     = "admin"
}

variable "enable_vault_config" {
  description = "Set false for the first apply, before Vault is reachable."
  type        = bool
  default     = true
}
