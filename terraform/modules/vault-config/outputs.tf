output "roles" {
  value = { for ns, r in vault_kubernetes_auth_backend_role.app : ns => r.role_name }
}
