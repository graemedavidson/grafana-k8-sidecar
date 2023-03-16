provider "kubernetes" {
  config_context_cluster = "kind-kind"
}

resource "kubernetes_manifest" "grafana_dashboard_crd" {
  field_manager {
    force_conflicts = true
  }

  manifest = {
    apiVersion = "apiextensions.k8s.io/v1"
    kind       = "CustomResourceDefinition"
    metadata = {
      name = "grafanadashboards.example.co.uk"
      /* namespace   = kubernetes_namespace.developers */
    }
    spec = yamldecode(templatefile("${path.module}/crd/grafana-dashboard-crd.yml", {}))
  }
}

### Gatekeeper

resource "kubernetes_manifest" "gatekeeper_grafana_dashboard_constraint_template" {
  field_manager {
    force_conflicts = true
  }

  manifest = {
    apiVersion = " templates.gatekeeper.sh/v1beta1"
    kind       = "ConstraintTemplate"
    metadata = {
      name = "grafanasidecaralloweddirs"
    }
    spec = yamldecode(templatefile("${path.module}/gatekeeper/constraint_template.yml", {}))
  }
}

resource "kubernetes_manifest" "gatekeeper_grafana_dashboard_constraint_developers" {
  field_manager {
    force_conflicts = true
  }

  manifest = {
    apiVersion = " constraints.gatekeeper.sh/v1beta1"
    kind       = "GrafanaSidecarAllowedDirs"
    metadata = {
      name = "grafanasidecaralloweddirs-developers"
    }
    spec = yamldecode(templatefile("${path.module}/gatekeeper/constraint_developers.yml", {}))
  }
}

resource "k8s_manifest" "gatekeeper_grafana_dashboard_constraint_developers" {
  name    = "grafanasidecaralloweddirs-developers"
  kind    = ""
  content = templatefile("${path.module}/gatekeeper/constraint_developers.yml", {})

  depends_on = [
    kubernetes_manifest.gatekeeper_grafana_dashboard_constraint_template,
  ]
}

resource "kubernetes_namespace" "developers" {
  metadata {
    name = "developers"
    labels = {
      "example.co.uk/team" = "developers"
    }
  }
}

locals {
  grafana_dashboards_path = "${path.module}/dashboards"
  dashboards = {
    "example" = { dir = "developers" }, # Success
    "example" = { dir = "fail" },       # fail due to gatekeeper contstraint
  }
}

module "infra_grafana_dashboard" {
  source = "../dashboard/"

  for_each = local.dashboards

  namespace = kubernetes_namespace.developers

  dashboard_name = each.key
  dashboard_dir  = each.value.dir
  dashboard_json = file("${path.module}/${local.grafana_dashboards_path}/${each.key}.json")

  depends_on = [
    kubernetes_manifest.grafana_dashboard_crd,
    kubernetes_namespace.developers,
  ]
}
