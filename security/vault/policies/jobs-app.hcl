# Least privilege: the application may only read its own database credentials.
path "secret/data/jobs-platform/database" {
  capabilities = ["read"]
}
path "secret/metadata/jobs-platform/database" {
  capabilities = ["read"]
}
