resource "kubernetes_manifest" "grafana_dashboard" {
  manifest = {
    apiVersion = "grafana.five.ai/v1"
    kind       = "GrafanaDashboard"

    metadata = {
      name        = var.dashboard_name
      namespace   = var.namespace
      labels      = var.labels
      annotations = var.annotations
    }

    spec = {
      name = var.dashboard_name
      dir  = var.dashboard_dir
      json = var.dashboard_json
    }
  }
}
