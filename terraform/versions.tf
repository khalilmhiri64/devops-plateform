terraform {
  required_version = ">= 1.6"

  required_providers {
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.35" }
    helm       = { source = "hashicorp/helm", version = "~> 2.17" }
    vault      = { source = "hashicorp/vault", version = "~> 4.5" }
    random     = { source = "hashicorp/random", version = "~> 3.6" }
  }

  # Local state is fine for a single-developer Docker Desktop cluster.
  # For a team, switch to a remote backend with locking (e.g. S3 + DynamoDB, or Terraform Cloud).
  backend "local" {
    path = "terraform.tfstate"
  }
}
