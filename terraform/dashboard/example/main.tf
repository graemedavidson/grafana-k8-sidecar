locals {
  labels = {
    "dummy" = "value"
  }

  annotations = {
    "dummy" = "value"
  }
}

module "grafana_dashboard" {
  source = "../"

  namespace      = "default"
  dashboard_name = "dummyvalue"
  dashboard_dir  = "dummyvalue"
  dashboard_json = "dummyvalue"

  labels      = local.labels
  annotations = local.annotations
}
