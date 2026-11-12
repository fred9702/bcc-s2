include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "envcommon" {
  path   = "${get_repo_root()}/infra/live/_envcommon/streamlit-app.hcl"
  expose = true
}

inputs = {
  ingress_host = "bcc-staging.localhost"
  namespace    = "bcc-staging"
  replicas     = 1
  max_replicas = 2
  extra_env    = { DEFAULT_TICKER = "VOD.L" }
}
