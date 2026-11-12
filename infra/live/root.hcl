# Root Terragrunt config: shared provider + state for every environment/unit.
locals {
  env_vars     = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  environment  = local.env_vars.locals.environment
  kube_context = get_env("KUBE_CONTEXT", local.env_vars.locals.kube_context)
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOT
    provider "kubernetes" {
      config_path    = pathexpand("${get_env("KUBECONFIG", "~/.kube/config")}")
      config_context = "${local.kube_context}"
    }
  EOT
}

# Local state for the minikube simulation. In a real cloud account this would be:
#
# remote_state {
#   backend = "s3"
#   generate = { path = "backend.tf", if_exists = "overwrite_terragrunt" }
#   config = {
#     bucket         = "bcc-tfstate-${local.environment}"
#     key            = "${path_relative_to_include()}/terraform.tfstate"
#     region         = "eu-west-2"
#     encrypt        = true
#     use_lockfile   = true   # S3-native locking (no DynamoDB table needed)
#   }
# }
remote_state {
  backend = "local"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    path = "${get_parent_terragrunt_dir()}/.state/${path_relative_to_include()}/terraform.tfstate"
  }
}

inputs = {
  environment = local.environment
}
