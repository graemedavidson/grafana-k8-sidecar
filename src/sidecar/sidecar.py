"""Kubernetes Grafana Sidecar."""

import asyncio
import collections
import contextlib
import json
import logging
import re
import signal
import sys
import threading
from pathlib import Path
from typing import Tuple

import click
import kopf
from prometheus_client import Counter, Gauge, start_http_server

import sidecar.exceptions as exceptions

# Local Libraries
from sidecar.dashboard_files import check_file, create_file, delete_file, update_file

# Globals
metrics_prefix = "k8s_grafana_sidecar"
resources_gauge = Gauge(f"{metrics_prefix}_resources", "Current number of resources")
error_gauge = Gauge(
    f"{metrics_prefix}_resource_errors",
    "Current number of resources which have encountered an error",
    ["error"],
)
error_counter = Counter(f"{metrics_prefix}_errors", "errors counter", ["error"])
create_counter = Counter(
    f"{metrics_prefix}_created_resources", "created resources counter"
)
delete_counter = Counter(
    f"{metrics_prefix}_deleted_resources", "delete resources counter"
)
update_counter = Counter(
    f"{metrics_prefix}_updated_resources", "updated resources counter", ["value"]
)
_working_dir = "/app/grafana-dashboards"
_max_workers = 20


@kopf.index("example.co.uk", "v1", "grafanadashboards")
def d_idx(uid: str, spec: object, **kwargs):
    """Return dashboard based on UID as index."""
    return {
        uid: {
            "dir": spec["dir"],
            "name": spec["name"],
        }
    }


@kopf.index("example.co.uk", "v1", "grafanadashboards")
def errors_idx(status: object, **kwargs):
    """Return status of error."""
    if "reason" in status and status["reason"] != "":
        return status["reason"]


@kopf.index("example.co.uk", "v1", "grafanadashboards")
def json_uids(uid: str, spec: object, logger: logging, **kwargs) -> object:
    """Return dashboard and uid."""
    try:
        dashboard_uid, _ = get_dashboard_json_meta(spec["json"])
        return {dashboard_uid: uid}
    except Exception as e:
        logger.error(f"unexpected error getting dashboard json meta: {e}")


@kopf.on.event("example.co.uk", "v1", "grafanadashboards")
def error_count(errors_idx: kopf.Index, logger: logging, **kwargs):
    """Return error count stored in prometheus metrics."""
    errors = errors_idx.get(None, [])
    error_count = collections.Counter(errors)
    error_gauge.clear()
    for error_name in error_count.elements():
        logger.info(f"error count (type: {error_name}): {error_count[error_name]}")
        error_gauge.labels(error_name).set(error_count[error_name])


@kopf.on.event("example.co.uk", "v1", "grafanadashboards")
def resource_count(d_idx: kopf.Index, logger: logging, **kwargs):
    """Update metrics with number of managed resources."""
    dashboard_count = len(d_idx)
    resources_gauge.set(dashboard_count)
    logger.info(f"dashboard resources: {dashboard_count}")


@kopf.timer("example.co.uk", "v1", "grafanadashboards", interval=86400, initial_delay=5)
def reconcile(
    json_uids: kopf.Index,
    patch: object,
    uid: str,
    spec: object,
    status: object,
    logger: logging,
    **kwargs,
):
    """Ensure all changes filesystem side reconciled with kubernetes state.

    Runs every 86400 seconds (24 hours)
    """
    # Do not attempt to reconcile files in an error state
    # ToDo: Should this be for all states?
    if "state" in status and status["state"] == "error":
        return

    filename = "{}.json".format(Path(spec["dir"], spec["name"]))

    try:
        check_file(_working_dir, filename, spec["json"])
    except exceptions.noFileExists as e:
        logger.warning(
            f"recreating missing file: {_working_dir}/{filename} ({uid}) - {e.code}"
        )
        create(json_uids, patch, uid, spec, logger)
    except exceptions.jsonMismatch as e:
        # have diasabled `update_file` as it would overwrite changes made to the dashboard
        # in the UI which assumed is intentional?
        # update_file(_working_dir, filename, None, spec['json'])
        logger.warning(
            f"json drift for: {filename} ({uid}) - currently configured not to reconcile drift"
        )
        patch.status["reason"] = e.code
        patch.status["state"] = "warning"
    except Exception as e:
        logger.info(f"unexpected error when checking file: {e}")

    logger.info("reconciled state: complete")


def get_dashboard_json_meta(dashboard_json: str) -> Tuple[str, str]:
    """Return the grafana title and grafana uid from json if valid, otherwise None.

    [json model](https://grafana.com/docs/grafana/latest/dashboards/json-model/)

    :param dashboard_json: json taken from k8s object (spec.json)
    :type dashboard_json: string
    :return: grafana uid, grafana title
    :rtype: string, string
    """
    try:
        dashboard_json = json.loads(dashboard_json)
    except ValueError:
        raise exceptions.invalidJson

    if "uid" not in dashboard_json:
        raise exceptions.invalidJsonNoUid
    elif len(dashboard_json["uid"]) > 40:
        raise exceptions.invalidJsonUidTooLong
    elif not re.match(r"^([\w\_\-])*$", dashboard_json["uid"]):
        raise exceptions.invalidJsonUidUnexpectedCharacters

    if "title" not in dashboard_json:
        raise exceptions.invalidJsonNoTitle
    elif not re.match(
        r"^[\w\_\-\s!£$%^&*+=#@:;,.\'\"~?(){}\[\]<>/]*$", dashboard_json["title"]
    ):
        raise exceptions.invalidJsonTitleUnexpectedCharacters

    return dashboard_json["uid"], dashboard_json["title"]


@kopf.on.create("example.co.uk", "v1", "grafanadashboards")
def create(
    json_uids: kopf.Index,
    patch: object,
    uid: str,
    spec: object,
    logger: logging,
    **kwargs,
):
    """Create new dashboards."""
    error = None

    create_counter.inc()

    filename = "{}.json".format(Path(spec["dir"], spec["name"]))

    try:
        dashboard_uid, dashboard_title = get_dashboard_json_meta(spec["json"])

        if dashboard_uid in json_uids and len(json_uids[dashboard_uid]) > 1:
            raise exceptions.duplicateDashboardUid
        if dashboard_title == spec["dir"]:
            raise exceptions.jsonTitleMatchesDirName
    except Exception as e:
        error = e.code
        logger.debug(f"{e.message}")

    if error is None:
        try:
            create_file(_working_dir, filename, spec["json"])
            patch.status["state"] = "ok"
            patch.status["reason"] = ""
            logger.info(f"created dashboard: {filename} ({uid})")
        except Exception as e:
            error = e.code
            logger.debug(f"{e.message}")

    if error is not None:
        patch.status["reason"] = error
        patch.status["state"] = "error"
        error_counter.labels(error).inc()
        logger.error(f"create dashboard: {filename} ({uid}) - failed: {error}")
        raise kopf.PermanentError(f"create dashboard failed: {error}")


@kopf.on.update("example.co.uk", "v1", "grafanadashboards")
def update(
    json_uids: kopf.Index,
    patch: object,
    uid: str,
    spec: object,
    status: object,
    old: object,
    new: object,
    diff: object,
    logger: logging,
    **kwargs,
):
    """Update dashboard which is currently in the state = ok.

    updates:
    * dir = change the place the file is located
    * name = filename change (not the name in grafana that changes)
    * json = update the content
    """
    error = None

    updates = [field[1] for op, field, old, new in diff]
    for update in updates:
        update_counter.labels(update).inc()
    logger.info(f"fields updates {updates} for {uid}")

    old_filename, new_filename, new_json = None, None, None
    old_filename = "{}.json".format(Path(old["spec"]["dir"], old["spec"]["name"]))
    # maybe use spec as new = spec, but potentially new could = None
    new_filename = "{}.json".format(Path(new["spec"]["dir"], new["spec"]["name"]))

    logger.debug(f"updated old filename: {old_filename} to {new_filename} ({uid})")
    # DO I LOG IN DEBUG MORE INFO - Operator might do this for me - check

    if "json" in updates:
        new_json = new["spec"]["json"]
        try:
            dashboard_uid, dashboard_title = get_dashboard_json_meta(new_json)

            if dashboard_uid in json_uids and len(json_uids[dashboard_uid]) > 1:
                raise exceptions.duplicateDashboardUid
            if dashboard_title == spec["dir"]:
                raise exceptions.jsonTitleMatchesDirName
        except Exception as e:
            error = e.code
            logger.debug(f"{e.message}")

    # Error Handling - [ ] move error handling into own function calling creates/updates
    if error is None and "state" in status and status["state"] == "error":
        logger.info(
            f'fixing error for: {_working_dir}/{spec["dir"]}/{spec["name"]} ({uid}), error: {status["reason"]}, updates: {updates}'
        )

        # currently it is expected that all error conditions will end with no file being created
        # or existing files deleted so this should always raise an exception at this time and use a
        # create.
        try:
            check_file(_working_dir, new_filename, None)
            logger.info(f"fixing error for: {uid} with update")
        except exceptions.noFileExists:
            logger.info(f"fixing error for: {uid} with create")
            create(json_uids, patch, uid, spec, logger)
            return
        except Exception as e:
            logger.debug(f"{e.message}")
            logger.info(
                f"unexpected check failure for: {new_filename} ({uid}) with error state: {e.code}"
            )

    # Updates
    if error is None:
        try:
            update_file(_working_dir, old_filename, new_filename, new_json)
            patch.status["state"] = "ok"
            patch.status["reason"] = ""
            logger.info(f"updated dashboard: {new_filename} ({uid}): {updates}")
        except exceptions.nothingToDo:
            logger.debug(
                f"updated dashboard: {new_filename} ({uid}): update found nothing to do, aborting operation."
            )
            return
        except Exception as e:
            error = e.code
            logger.debug(f"{e.message}")

    if error is not None:
        patch.status["reason"] = error
        patch.status["state"] = "error"
        error_counter.labels(error).inc()
        logger.error(
            f"updated dashboard: {new_filename} ({uid}) for updates {updates} - failed: {error}"
        )
        logger.error(f"deleting original ({old_filename}) file due to error ({uid})")
        delete(uid, old["spec"], status, logger)

        raise kopf.PermanentError(f"create failed: {error}")


@kopf.on.delete("example.co.uk", "v1", "grafanadashboards")
def delete(uid: str, spec: object, status: object, logger: logging, **kwargs):
    """Delete a dashboard."""
    delete_counter.inc()

    filename = "{}.json".format(Path(spec["dir"], spec["name"]))

    if "state" in status and status["state"] == "error":
        logger.info(f"fixing error for: {uid} with delete")

    try:
        delete_file(_working_dir, filename)
        logger.info(
            f'deleted dashboard: {_working_dir}/{spec["dir"]}/{spec["name"]} ({uid})'
        )
    except Exception as e:
        # As kubernetes resource is deleted do not add active error
        logger.error(f"unexpected error occurred during delete: {e}")


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **kwargs):
    """Perform all necessary startup tasks here.

    Keep them lightweight and relevant as the other handlers won't be initialized
    until these tasks are complete.
    https://kopf.readthedocs.io/en/latest/configuration/
    """
    settings.persistence.finalizer = (
        "kopf.nolar.org/GrafanaDashboardSidecarFinalizerMarker"
    )
    settings.peering.standalone = True
    settings.execution.max_workers = _max_workers
    settings.batching.error_delays = [10, 20, 30]

    settings.watching.connect_timeout = 1 * 60
    settings.watching.server_timeout = 30 * 60
    settings.watching.client_timeout = 35 * 60


def kopf_thread(ready_flag: threading.Event, stop_flag: threading.Event):
    """K8s Operator thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with contextlib.closing(loop):
        # Default to clusterwide - can make this configurable for different use cases
        scope = {"clusterwide": True, "namespaces": []}

        loop.run_until_complete(
            kopf.operator(
                liveness_endpoint=None,
                clusterwide=scope["clusterwide"],
                namespaces=scope["namespaces"],
                ready_flag=ready_flag,
                stop_flag=stop_flag,
            )
        )


@click.command()
@click.option(
    "--working-dir",
    default="/app/grafana-dashboards",
    help="working directory to work with dashboard files",
)
@click.option(
    "--max-workers",
    default=20,
    help="number of synchronous workers used by the operator for synchronous handlers",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], case_sensitive=True
    ),
    envvar="LOG_LEVEL",
    default="INFO",
    help="Application logging level",
)
@click.option(
    "--prom-http-port", default=8000, help="port to publish prometheus metrics"
)
def scan(working_dir: str, max_workers: int, log_level: str, prom_http_port: int):
    """Scan for new Grafana Dashboard resources."""
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    click.echo("log level: {}".format(log_level))

    # using globals until best practice for passing through
    global _max_workers, _working_dir

    if not Path(working_dir).is_dir():
        click.echo(f"working dir: {working_dir} does not exist!")
        sys.exit(2)

    click.echo("Max Workers: {}".format(max_workers))
    _max_workers = max_workers

    click.echo("Working Dir: {}".format(working_dir))
    _working_dir = working_dir

    # Start Prometheus Metrics Server - might do this though Flask
    # Must be stated before starting the kopf thread below
    logging.info(
        "prometheus http started locally: http://localhost:{}".format(prom_http_port)
    )
    start_http_server(prom_http_port)

    ready_flag = threading.Event()
    stop_flag = threading.Event()
    try:
        thread = threading.Thread(
            target=kopf_thread,
            kwargs=dict(
                stop_flag=stop_flag,
                ready_flag=ready_flag,
            ),
        )
        thread.start()
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        print("\n! Received keyboard interrupt, quitting threads.\n")
        stop_flag.set()
        sys.exit()


if __name__ == "__main__":
    scan()
