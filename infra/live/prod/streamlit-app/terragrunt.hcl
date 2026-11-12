include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "envcommon" {
  path   = "${get_repo_root()}/infra/live/_envcommon/streamlit-app.hcl"
  expose = true
}

inputs = {
  namespace    = "bcc-prod"
  replicas     = 2
  max_replicas = 5
  resources = {
    requests = { cpu = "250m", memory = "384Mi" }
    limits   = { cpu = "1", memory = "768Mi" }
  }
  extra_env = { DEFAULT_TICKER = "VOD.L" }
}
