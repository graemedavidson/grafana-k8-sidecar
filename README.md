# Grafana Kubernetes Sidecar

**Archived:** due to no longer supporting within a deployment and never given any more time to tackle its
many issues and bugs.

Kubernetes sidecar installed alongside Grafana to deploy dashboards. Utilises shared volume between sidecar
and Grafana containers. Grafana automatically detects new Dashboards placed into configured [data source](https://grafana.com/docs/grafana/latest/administration/provisioning/#data-sources).

Replacement for sidecar included with the [Helm Prometheus Monitoring Stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack).

- Kubernetes Custom Resource Definition for Grafana Dashboard.
- Utilises the [Kopf](https://kopf.readthedocs.io/en/stable/) framework.
- Example Gatekeeper configuration for constraints on dashboard resources.
* local development environment setup for testing and development

## Documentation

[Documentation](./docs/)

## Releases

- Changes introduced through PRs.
  - update [changelog](./CHANGELOG.md), [readme](./README.md) and [documentation](./docs)
- Tag against `main` branch.
  - [Semantic Versioning](https://semver.org/) prefixing with a `v`.
- Include auto generated release notes curating where necessary.

## Setup for Development

```sh
virtualenv venv
source venv/bin/activate             # activate the venv
```

Install dependencies defined in [setup.py](./setup.py).

```sh
pip install --editable .[dev]        # install dependencies including dev dependencies
```

Create testable executable: `grafana-k8-sidecar`


### Kubernetes Cluster

Following documentation makes use of [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) for
a local K8 cluster to allow for testing.

[Kind Images](https://hub.docker.com/r/kindest/node/tags?page=1&ordering=last_updated)

```bash
kind create cluster --wait 5m     # specific version: `--image=kindest/node:<VERSION>`
export KUBE_CTX=kind-kind         # set kubectl to use kind cluster
kind delete cluster               # `--name` to delete specific cluster
```

Install latest Gatekeeper [release]( https://github.com/open-policy-agent/gatekeeper/releases):

```sh
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/<VERSION>/deploy/gatekeeper.yaml
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/<VERSION>/demo/basic/sync.yaml
```

Run [Terraform](https://www.terraform.io/) deployment.

```sh
cd ./terraform
terraform init
terraform apply
```

Review Grafana Dashboard resources created as part of Terraform deployment.

```sh
kubectl get grafanadashboards --all-namespaces
```

### Runtime

```sh
source venv/bin/activate  # activate the venv
grafana-k8-sidecar        # this will use defaults (max-workers: 20, working-dir: /tmp/grafana-dashboards)
```

Settings:

- `--working-dir=./sidecar/tests/fixtures/dashboards` to the dashboard fixtures.
- `--max-workers=1` max workers to 1 for easier chronological debugging.

Sidecar exposes [prometheus metrics](http://localhost:8000).

## Tests

- [unit](./tests/unit/)
  - `pytest`
  - configured to run as part of pre-commit config.
- [system](./tests/system-tests/)
  - `pytest -W ignore`
  - ToDo: currently broken and set to ignore.
- [fixtures](./tests/fixtures/)

## Docker Compose

Local monitoring setup for testing metrics created by service.

```sh
cd local                    # dir with docker-compose and config files
docker-compose up           # bring up the containers
docker-compose down -v      # tear down containers and remove volumes
```

Available services:

- [grafana](http://localhost:3000)
  - username: `admin`,
  - password: `test`
- [prometheus](http://localhost:9000)
