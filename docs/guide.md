# Using Grafana K8 Sidecar

Commands and configuration for making use of the Grafana Sidecar to load dashboards.

## List/View/Edit

```sh
kubectl get grafanadashboards
kubectl get grafanadashboards <dashboard> -o yaml
kubectl edit grafanadashboards <dashboard>
```

Example Output:

```sh
# OK
NAME         REASON        STATE   UPDATED   AGE   DIRECTORY   FILENAME     UID
example      ok                              1m    example     example      ABC123...

# Error
NAME         REASON        STATE   UPDATED   AGE   DIRECTORY   FILENAME     UID
test         invalid_json  error             1m    test        test         ABC123...
```

#### Error Codes

[Source](../src/sidecar/exceptions.py)

| Error Code                                 | State (ok/error)   | Description
| ---                                        | ---                | ---
| `ok`                                       | `ok`               | dashboard has been deployed successfully.
| `json_title_matches_dir_name`              | `error`            | the title in the dashboard json matches the dir name in the k8s object, which grafana does not allow
| `duplicate_dashboard_uid`                  | `error`            | the UID fin the dashboard json has been used by another dashboard
| `no_file_exists`                           | `error`            | when attempting a delete of dashboard the expected file is not found
| `json_mismatch`                            | `error`            | json on the filesystem is different from the kubernetes resource
| `invalid_json`                             | `error`            | json in kubernetes resource is invalid
| `invalid_json_no_title`                    | `error`            | no title found in dashboard json
| `invalid_json_no_uid`                      | `error`            | no UID found in dashboard json
| `invalid_json_uid_too_long`                | `error`            | UID too long (> 40 chars) in dashboard json
| `invalid_json_uid_unexpected_characters`   | `error`            | UID has unexpected characters in dashboard json
| `invalid_json_title_unexpected_characters` | `error`            | title has unexpected characters in dashboard json
| `nothing_to_do`                            | `ok`               | No changes found when comparing File system dashboard and Kubernetes resource
| `duplicate_name`                           | `error`            | the dir/name fields in kubernetes resource is used by another resource
| `parent_dir_does_not_exist`                | `error`            | dir field in kubernetes resource does not exist
| `old_path_does_not_exist`                  | `error`            | when updating dashboard the old path does not exist
| `path_not_dir`                             | `error`            | dir field in kubernetes resource is not a directory
| `dir_not_empty`                            | `error`            | when attempting to delete a directory it is found not empty

## Adding a Dashboard

To add a dashboard to your deployment add the following sets of configuration with attention to the following
rules/constraints:

Terraform/Kubernetes resource:

Review [Custom Resource Definition](../terraform/crd/grafana-dashboard-crd.yml){target=_blank}.

* required fields:
    * `spec.name`
    * `spec.dir`
    * `spec.json`
* `spec.name` and `spec.dir` must be unique pairing as to not conflict with another dashboard
* `spec.name` and `spec.dir` have regex rules
  * `spec.name`: `^([\w\_\-\s])*$`
    - [test](https://pythex.org/?regex=%5E(%5B%5Cw%5C_%5C-%5Cs%5D)*%24&test_string=1111111111%0A1%26%0A1h7930%0Atest%20test&ignorecase=0&multiline=1&dotall=0&verbose=0){target=_blank}
  * `spec.dir`: `^([\w\_\-])*$`
    - [test](https://pythex.org/?regex=%5E(%5B%5Cw%5C_%5C-%5D)*%24&test_string=1111111111%0A1%26%0A1h7930&ignorecase=0&multiline=1&dotall=0&verbose=0){target=_blank}

JSON payload:

* required fields:
    * `title`
    * `uid`
* json `title` can't be the same as `spec.dir` - Grafana rule.
* json `title` regex: `^[\w\_\-\s!£$%^&*+=#@:;,.\'\"~?(){}\[\]<>/]*$`
  - [test](https://pythex.org/?regex=%5E%5B%5Cw%5C_%5C-%5Cs!%C2%A3%24%25%5E%26*%2B%3D%23%40%3A%3B%2C.%5C%27%5C%22~%3F()%7B%7D%5C%5B%5C%5D%3C%3E%2F%5D*%24&test_string=test%0Atest%2Ftest%0Atest%60test&ignorecase=0&multiline=1&dotall=0&verbose=0){target=_blank}
* json `uid` must be unique
* json `uid` max character limit: 40
* json `uid` regex: `^([\w\_\-])*$`
  - [test](https://pythex.org/?regex=%5E(%5B%5Cw%5C_%5C-%5D)*%24&test_string=1111111111%0A1%26%0A1h7930&ignorecase=0&multiline=1&dotall=0&verbose=0){target=_blank}

### Grafana Directory Structure

[Source](../terraform/gatekeeper/)

| Grafana Directory   | Expected Team Use | Restricting namespace label
| ---                 | ---               | ---
| `development`       | developers        | `= example.co.uk/team: developers`
| `admin`             | admins            | `= example.co.uk/team: admins`

### Example Source Code

`main.tf`:

```hcl
provider "k8s" {
    kubeconfig_context = "<pin-cluster>"
}

module "grafana_dashboard" {
    source = ""

    namespace = "default"

    dashboard_name = "example1"
    dashboard_dir  = "example1"
    dashboard_json = file("${path.module}/grafana-dashboard.json")
}
```
