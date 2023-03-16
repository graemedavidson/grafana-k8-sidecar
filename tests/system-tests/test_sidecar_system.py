import os.path
import subprocess
import time

import kopf
import pytest
from kopf.testing import KopfRunner

sidecar_py = os.path.relpath(
    os.path.join(os.path.dirname(__file__), "../../", "src/sidecar.py")
)


# Review: https://kind.sigs.k8s.io/


@pytest.fixture(scope="session")
def crd_yaml():
    """Dashboard Custom Resource Definition for Kubernetes"""
    return os.path.relpath(
        os.path.join(
            os.path.dirname(__file__),
            "../../../",
            "terraform/crd/grafana-dashboard-crd.yml",
        )
    )


@pytest.fixture()
def dashboard_yaml():
    """Test Dashboard Resource"""
    return os.path.relpath(
        os.path.join(os.path.dirname(__file__), "../fixtures/k8s-objects/test-1.yml")
    )


@pytest.mark.systemtest
@pytest.mark.skip(reason="Incomplete test")
def test_resource_lifecycle(crd_yaml, dashboard_yaml):
    settings = kopf.OperatorSettings()
    settings.watching.server_timeout = 10
    settings.batching.worker_limit = 1
    with KopfRunner(
        ["run", "-A", "--verbose", "--dev", sidecar_py], timeout=60, settings=settings
    ) as runner:
        subprocess.run(
            f"kubectl create -f {crd_yaml}",
            shell=False,
            check=False,
            timeout=10,
            capture_output=True,
        )
        time.sleep(1)

        subprocess.run(
            f"kubectl create -f {dashboard_yaml}",
            shell=False,
            check=True,
            timeout=10,
            capture_output=True,
        )
        time.sleep(1)

        subprocess.run(
            f"kubectl delete -f {dashboard_yaml}",
            shell=False,
            check=True,
            timeout=10,
            capture_output=True,
        )
        time.sleep(1)

    assert runner.exc_info
    assert runner.exc_info[0] is SystemExit
    assert runner.exc_info[1].code == 0
    assert runner.exit_code == 0
    assert runner.exception is None

    # assert runner.output.startswith("Usage:")
    # assert runner.stdout.startswith("Usage:")

    # log level: WARNING
    # max workers: 20
    # working dir: /tmp/grafana-dashboards

    # # There are usually more than these messages, but we only check for the certain ones.
    # assert '[default/kopf-example-1] Creation event:' in runner.stdout
    # assert '[default/kopf-example-1] Something was logged here.' in runner.stdout
