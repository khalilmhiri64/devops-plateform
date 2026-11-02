variable "namespaces" {
  description = "Application namespaces that get their own credentials and Vault role."
  type        = list(string)
}

variable "policy_dir" {
  description = "Directory holding the HCL policy files."
  type        = string
}
