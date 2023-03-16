# Dashboard

## Known Issues
There is currently a bug which will cause the Terraform apply to fail with spurious errors caused by using any single quote characters `'` in the json template.

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
### Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.4 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | >= 2.0.0 |

### Providers

| Name | Version |
|------|---------|
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | >= 2.0.0 |

### Modules

No modules.

### Resources

| Name | Type |
|------|------|
| [kubernetes_manifest.grafana_dashboard](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/resources/manifest) | resource |

### Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_annotations"></a> [annotations](#input\_annotations) | Map of annotations to be added to resource metadata. | `map(string)` | `{}` | no |
| <a name="input_dashboard_dir"></a> [dashboard\_dir](#input\_dashboard\_dir) | filesystem directory name for the dashboard to be created in, will create dir if it does not exist. | `string` | n/a | yes |
| <a name="input_dashboard_json"></a> [dashboard\_json](#input\_dashboard\_json) | json payload for dashboard. | `string` | n/a | yes |
| <a name="input_dashboard_name"></a> [dashboard\_name](#input\_dashboard\_name) | kubernetes resource name and filesystem filename for the dashboard. | `string` | n/a | yes |
| <a name="input_labels"></a> [labels](#input\_labels) | Map of labels to be added to resource metadata. | `map(string)` | `{}` | no |
| <a name="input_namespace"></a> [namespace](#input\_namespace) | namespace to deploy dashboard. | `string` | n/a | yes |

### Outputs

No outputs.
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
