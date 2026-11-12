# Shared definition of the streamlit-app unit; envs include this and override inputs.
locals {
  repo_root = get_repo_root()
}

terraform {
  source = "${get_repo_root()}/infra/modules/streamlit-app"
}

inputs = {
  name      = "bcc-dashboard"
  image     = get_env("IMAGE", "bcc-s2")
  image_tag = get_env("IMAGE_TAG", "local")
  data_files = {
    "prices.csv"      = "${local.repo_root}/data/prices.csv"
    "vol_surface.csv" = "${local.repo_root}/data/vol_surface.csv"
  }
}
