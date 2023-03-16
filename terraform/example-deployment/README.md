# TF Docs

`tf-docs markdown table --indent 2 . | tee >> README.md`

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_grafana"></a> [grafana](#requirement\_grafana) | ~> 1.10 |
| <a name="requirement_k8s"></a> [k8s](#requirement\_k8s) | 0.2.2 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_grafana"></a> [grafana](#provider\_grafana) | 1.13.0 |
| <a name="provider_k8s"></a> [k8s](#provider\_k8s) | 0.2.2 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_grafana_dashboard"></a> [grafana\_dashboard](#module\_grafana\_dashboard) | git::ssh://git@gitlab.corp.five.ai/infra/tf-mod/k8s-grafana-sidecar-dashboard.git | v0.1.0 |

## Resources

| Name | Type |
|------|------|
| [grafana_dashboard.test-1](https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/dashboard) | resource |
| [grafana_dashboard.test-2](https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/dashboard) | resource |
| [grafana_folder.gp-1](https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/folder) | resource |
| [grafana_folder.gp-2](https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/folder) | resource |
| [k8s_manifest.gatekeeper_grafana_dashboard_constraint_eng](https://registry.terraform.io/providers/fiveai/k8s/0.2.2/docs/resources/manifest) | resource |
| [k8s_manifest.gatekeeper_grafana_dashboard_constraint_infra](https://registry.terraform.io/providers/fiveai/k8s/0.2.2/docs/resources/manifest) | resource |
| [k8s_manifest.gatekeeper_grafana_dashboard_constraint_template](https://registry.terraform.io/providers/fiveai/k8s/0.2.2/docs/resources/manifest) | resource |
| [k8s_manifest.grafana_dashboard_crd](https://registry.terraform.io/providers/fiveai/k8s/0.2.2/docs/resources/manifest) | resource |

## Inputs

No inputs.

## Outputs

No outputs.
<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
### Requirements

No requirements.

### Providers

| Name | Version |
|------|---------|
| <a name="provider_k8s"></a> [k8s](#provider\_k8s) | n/a |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | n/a |

### Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_infra_grafana_dashboard"></a> [infra\_grafana\_dashboard](#module\_infra\_grafana\_dashboard) | ../dashboard/ | n/a |

### Resources

| Name | Type |
|------|------|
| [k8s_manifest.gatekeeper_grafana_dashboard_constraint_developers](https://registry.terraform.io/providers/hashicorp/k8s/latest/docs/resources/manifest) | resource |
| [kubernetes_manifest.gatekeeper_grafana_dashboard_constraint_developers](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/resources/manifest) | resource |
| [kubernetes_manifest.gatekeeper_grafana_dashboard_constraint_template](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/resources/manifest) | resource |
| [kubernetes_manifest.grafana_dashboard_crd](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/resources/manifest) | resource |
| [kubernetes_namespace.developers](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/resources/namespace) | resource |

### Inputs

No inputs.

### Outputs

No outputs.
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
