# Jenkins can read CI-only secrets (registry creds, git token), nothing else.
path "secret/data/ci/*" {
  capabilities = ["read"]
}
