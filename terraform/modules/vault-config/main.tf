# Generate the DB password once and store it in Vault only; the Vault Secrets
# Operator syncs it into each namespace. Nothing sensitive is committed to Git.
resource "random_password" "db" {
  for_each = toset(var.namespaces)
  length   = 32
  special  = false
}

resource "vault_kv_secret_v2" "db" {
  for_each = toset(var.namespaces)
  mount    = "secret"
  # One path per namespace so staging and production never share credentials.
  name = "${each.key}/jobs-platform/database"
  data_json = jsonencode({
    username     = "jobs"
    password     = random_password.db[each.key].result
    database_url = "postgresql://jobs:${random_password.db[each.key].result}@postgres:5432/jobs"
  })
}

resource "vault_auth_backend" "kubernetes" {
  type = "kubernetes"
}

resource "vault_kubernetes_auth_backend_config" "this" {
  backend         = vault_auth_backend.kubernetes.path
  kubernetes_host = "https://kubernetes.default.svc"
}

resource "vault_policy" "app" {
  for_each = toset(var.namespaces)
  name     = "jobs-app-${each.key}"
  # Base policy file, re-rooted under the namespace-specific path.
  policy = replace(file("${var.policy_dir}/jobs-app.hcl"), "secret/data/jobs-platform", "secret/data/${each.key}/jobs-platform")
}

resource "vault_policy" "ci" {
  name   = "ci"
  policy = file("${var.policy_dir}/ci.hcl")
}

resource "vault_kubernetes_auth_backend_role" "app" {
  for_each                         = toset(var.namespaces)
  backend                          = vault_auth_backend.kubernetes.path
  role_name                        = "jobs-app-${each.key}"
  bound_service_account_names      = ["jobs-app"]
  bound_service_account_namespaces = [each.key]
  token_policies                   = [vault_policy.app[each.key].name]
  token_ttl                        = 3600
  audience                         = "vault"
}
