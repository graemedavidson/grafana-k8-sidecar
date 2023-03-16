import json
import logging
from pathlib import Path
from unittest.mock import MagicMock

import kopf
import pytest
from prometheus_client import REGISTRY

import sidecar.exceptions as exceptions

# local library
from sidecar.sidecar import (
    create,
    delete,
    error_count,
    get_dashboard_json_meta,
    reconcile,
    resource_count,
    update,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGGER = logging.getLogger(__name__)
metrics_prefix = "k8s_grafana_sidecar"


def open_json_fixture(fixture_file):
    """
    load json from an existing fixture to use in the new file
    """
    path = Path(BASE_DIR, "tests/fixtures/dashboards", fixture_file)
    if not path.is_file():
        pytest.fail(f"no fixture found at {path}")
    return path.read_text()


@pytest.fixture()
def fixture_dir(tmp_path):
    """Copy fixture files into a tempdir for tests"""
    fixture_path = Path(BASE_DIR, "tests/fixtures/dashboards")
    tmp_dir = Path(tmp_path, "dashboards")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for fixture in fixture_path.rglob("*.json"):
        if fixture.parent.name == "dashboards":
            Path(tmp_dir, fixture.name).write_text(fixture.read_text())
            continue

        Path(tmp_dir, fixture.parent.name).mkdir(parents=True, exist_ok=True)
        Path(tmp_dir, fixture.parent.name, fixture.name).write_text(fixture.read_text())

    # Create empty dir
    Path(tmp_dir, "dir3").mkdir(parents=True, exist_ok=True)
    Path(tmp_dir, "invalid-json.json").write_text(INVALID_JSON)

    return Path(tmp_dir)


UID = "c145c09b-b030-433d-9b9c-e1385e0683c6"
TEST_1_JSON = open_json_fixture("test-1.json")
TEST_2_JSON = open_json_fixture("dir1/test-2.json")
INVALID_JSON = "invalid json"


# Create Tests
@pytest.mark.parametrize(
    "json_uids, spec, expected_path, expected_json, expected_log_status, expected_log_message",
    [
        (
            {},
            {"dir": "create-ok", "name": "create-ok", "json": TEST_2_JSON},
            # expected results
            "create-ok/create-ok.json",
            TEST_2_JSON,
            "INFO",
            "created dashboard",
        ),
    ],
)
def test_create_pass(
    monkeypatch,
    fixtures_dir,
    caplog,
    json_uids,
    spec,
    expected_path,
    expected_json,
    expected_log_status,
    expected_log_message,
):
    """Test create pass."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixtures_dir)

    before = REGISTRY.get_sample_value(f"{metrics_prefix}_created_resources_total")

    with caplog.at_level(logging.INFO):
        create(json_uids, MagicMock(), UID, spec, LOGGER)

    after = REGISTRY.get_sample_value(f"{metrics_prefix}_created_resources_total")
    assert 1 == (after - before)

    assert UID in caplog.text
    assert expected_log_status in caplog.text
    assert expected_log_message in caplog.text

    p = Path(fixtures_dir, expected_path)
    assert p.is_file() is True
    assert json.loads(p.read_text()) == json.loads(expected_json)


@pytest.mark.parametrize(
    "json_uids, spec, expected_error",
    [
        (
            {},
            {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON},
            "duplicate_name",
        ),
        (
            {
                "222222222": [
                    "00000000-aaaa-aaaa-aaaa-000000000000",
                    "00000001-aaaa-aaaa-aaaa-000000000000",
                ]
            },
            {"dir": "dir3", "name": "test-4", "json": TEST_2_JSON},
            "duplicate_dashboard_uid",
        ),
        (
            {},
            {"dir": "test-2", "name": "test-2", "json": TEST_2_JSON},
            "json_title_matches_dir_name",
        ),
        (
            {},
            {
                "dir": "test-2",
                "name": "test-2",
                "json": '{ "title": "test-1", "uid": "11111111111111111111111111111111111111111" }',
            },
            "invalid_json_uid_too_long",
        ),
        (
            {},
            {"dir": "test-2", "name": "test-2", "json": '{ "title": "test-1" }'},
            "invalid_json_no_uid",
        ),
        (
            {},
            {"dir": "test-2", "name": "test-2", "json": '{ "uid": "111111111" }'},
            "invalid_json_no_title",
        ),
        (
            {},
            {
                "dir": "test-2",
                "name": "test-2",
                "json": '{ "title": "create`fail", "uid": "111111111" }',
            },
            "invalid_json_title_unexpected_characters",
        ),
        (
            {},
            {
                "dir": "test-2",
                "name": "test-2",
                "json": '{ "title": "create", "uid": "1111/11111" }',
            },
            "invalid_json_uid_unexpected_characters",
        ),
    ],
)
def test_create_fail(
    monkeypatch, fixtures_dir, caplog, json_uids, spec, expected_error
):
    """Test create fail."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixtures_dir)

    # set to 0 if this metric is empty
    before = (
        REGISTRY.get_sample_value(
            f"{metrics_prefix}_errors_total", {"error": expected_error}
        )
        or 0
    )

    with caplog.at_level(logging.INFO), pytest.raises(kopf.PermanentError):
        create(json_uids, MagicMock(), UID, spec, LOGGER)

    after = REGISTRY.get_sample_value(
        f"{metrics_prefix}_errors_total", {"error": expected_error}
    )
    assert 1 == (after - before)

    assert UID in caplog.text
    # Log Level
    assert "ERROR" in caplog.text
    assert f"failed: {expected_error}" in caplog.text


# Update Tests
@pytest.mark.parametrize(
    "json_uids, spec, status, old, new, diff, expected_updates, expected_path, expected_json",
    [
        # json change
        (
            {},
            {"dir": "dir1", "name": "test-2", "json": TEST_1_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_1_JSON}},
            (("change", ("spec", "json"), TEST_2_JSON, TEST_1_JSON),),
            # expected results
            ["json"],
            "dir1/test-2.json",
            TEST_1_JSON,
        ),
        # name change
        (
            {},
            {"dir": "dir1", "name": "name-change", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "dir1", "name": "name-change", "json": TEST_2_JSON}},
            (("change", ("spec", "name"), "test-2", "name-change"),),
            # expected results
            ["name"],
            "dir1/name-change.json",
            TEST_2_JSON,
        ),
        # dir change
        (
            {},
            {"dir": "change-dir", "name": "test-2", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "change-dir", "name": "test-2", "json": TEST_2_JSON}},
            (("change", ("spec", "dir"), "dir1", "change-dir"),),
            # expected results
            ["dir"],
            "change-dir/test-2.json",
            TEST_2_JSON,
        ),
        # dir + name change
        (
            {},
            {"dir": "change-dir", "name": "change-name", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "change-dir", "name": "change-name", "json": TEST_2_JSON}},
            (
                ("change", ("spec", "dir"), "dir1", "change-dir"),
                ("change", ("spec", "name"), "test-2", "change-name"),
            ),
            # expected results
            ["dir", "name"],
            "change-dir/change-name.json",
            TEST_2_JSON,
        ),
        # all change
        (
            {},
            {"dir": "change-dir", "name": "change-name", "json": TEST_1_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "change-dir", "name": "change-name", "json": TEST_1_JSON}},
            (
                ("change", ("spec", "json"), TEST_2_JSON, TEST_1_JSON),
                ("change", ("spec", "dir"), "dir1", "all-change"),
                ("change", ("spec", "name"), "test-2", "all-change"),
            ),
            # expected results
            ["dir", "name", "json"],
            "change-dir/change-name.json",
            TEST_1_JSON,
        ),
    ],
)
def test_update_pass(
    monkeypatch,
    fixtures_dir,
    caplog,
    json_uids,
    spec,
    status,
    old,
    new,
    diff,
    expected_updates,
    expected_path,
    expected_json,
):
    """Test update all pass."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixtures_dir)

    metrics_before = {}
    for metric_update in expected_updates:
        # set to 0 if this metric is empty
        metrics_before[metric_update] = (
            REGISTRY.get_sample_value(
                f"{metrics_prefix}_updated_resources_total", {"value": metric_update}
            )
            or 0
        )

    with caplog.at_level(logging.INFO):
        update(json_uids, MagicMock(), UID, spec, status, old, new, diff, LOGGER)

    for metric_update in expected_updates:
        after = REGISTRY.get_sample_value(
            f"{metrics_prefix}_updated_resources_total", {"value": metric_update}
        )
        assert 1 == (after - metrics_before[metric_update])

    assert UID in caplog.text
    assert "INFO" in caplog.text
    assert "updated dashboard" in caplog.text

    p = Path(fixtures_dir, expected_path)
    assert p.is_file() is True
    assert json.loads(p.read_text()) == json.loads(expected_json)


@pytest.mark.parametrize(
    "json_uids, spec, status, old, new, diff, expected_updates, expected_path, expected_json",
    [
        # nothing to do
        (
            {},
            {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            (("change", ("spec", "dir"), "dir1", "dir1"),),
            # expected results
            ["dir"],
            "dir1/test-2.json",
            TEST_2_JSON,
        ),
    ],
)
def test_update_pass_nothing_to_do(
    monkeypatch,
    fixtures_dir,
    caplog,
    json_uids,
    spec,
    status,
    old,
    new,
    diff,
    expected_updates,
    expected_path,
    expected_json,
):
    """Test update pass no action."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixtures_dir)

    metrics_before = {}
    for metric_update in expected_updates:
        # set to 0 if this metric is empty
        metrics_before[metric_update] = (
            REGISTRY.get_sample_value(
                f"{metrics_prefix}_updated_resources_total", {"value": metric_update}
            )
            or 0
        )

    with caplog.at_level(logging.DEBUG):
        update(json_uids, MagicMock(), UID, spec, status, old, new, diff, LOGGER)

    for metric_update in expected_updates:
        after = REGISTRY.get_sample_value(
            f"{metrics_prefix}_updated_resources_total", {"value": metric_update}
        )
        assert 1 == (after - metrics_before[metric_update])

    assert UID in caplog.text
    assert "DEBUG" in caplog.text
    assert "updated dashboard" in caplog.text
    assert "nothing to do" in caplog.text

    p = Path(fixtures_dir, expected_path)
    assert p.is_file() is True
    assert json.loads(p.read_text()) == json.loads(expected_json)


@pytest.mark.parametrize(
    "json_uids, spec, status, old, new, diff, expected_error",
    [
        (
            {},
            {"dir": "dir1", "name": "test-3", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "dir1", "name": "test-3", "json": TEST_2_JSON}},
            (("change", ("spec", "name"), "test-2", "test-3"),),
            # expected results
            "duplicate_name",
        ),
        (
            {},
            {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "dir1", "name": "test-2", "json": INVALID_JSON}},
            (("change", ("spec", "json"), TEST_2_JSON, INVALID_JSON),),
            # expected results
            "invalid_json",
        ),
        (
            {},
            {"dir": "dir4", "name": "nofile", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir3", "name": "nofile", "json": TEST_2_JSON}},
            {"spec": {"dir": "dir4", "name": "nofile", "json": TEST_2_JSON}},
            (("change", ("spec", "dir"), "dir3", "dir4"),),
            # expected results
            "old_path_does_not_exist",
        ),
        (
            {},
            {
                "dir": "dir1",
                "name": "test-2",
                "json": '{ "title": "test-1", "uid": "11111111111111111111111111111111111111111" }',
            },
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {
                "spec": {
                    "dir": "dir1",
                    "name": "test-2",
                    "json": '{ "title": "test-1", "uid": "11111111111111111111111111111111111111111" }',
                }
            },
            (
                (
                    "change",
                    ("spec", "json"),
                    TEST_2_JSON,
                    '{ "title": "test-1", "uid": "11111111111111111111111111111111111111111" }',
                ),
            ),
            # expected results
            "invalid_json_uid_too_long",
        ),
        (
            {},
            {"dir": "dir1", "name": "test-2", "json": '{ "title": "test-1" }'},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {
                "spec": {
                    "dir": "dir1",
                    "name": "test-2",
                    "json": '{ "title": "test-1" }',
                }
            },
            (("change", ("spec", "json"), TEST_2_JSON, '{ "title": "test-1" }'),),
            # expected results
            "invalid_json_no_uid",
        ),
        (
            {},
            {"dir": "dir1", "name": "test-2", "json": '{ "uid": "111111111" }'},
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {
                "spec": {
                    "dir": "dir1",
                    "name": "test-2",
                    "json": '{ "uid": "111111111" }',
                }
            },
            (("change", ("spec", "json"), TEST_2_JSON, '{ "uid": "111111111" }'),),
            # expected results
            "invalid_json_no_title",
        ),
        (
            {},
            {
                "dir": "dir1",
                "name": "test-2",
                "json": '{ "title": "create`fail", "uid": "111111111" }',
            },
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {
                "spec": {
                    "dir": "dir1",
                    "name": "test-2",
                    "json": '{ "title": "create`fail", "uid": "111111111" }',
                }
            },
            (
                (
                    "change",
                    ("spec", "json"),
                    TEST_2_JSON,
                    '{ "title": "create`fail", "uid": "111111111" }',
                ),
            ),
            # expected results
            "invalid_json_title_unexpected_characters",
        ),
        (
            {},
            {
                "dir": "dir1",
                "name": "test-2",
                "json": '{ "title": "create", "uid": "1111/11111" }',
            },
            {"reason": "", "state": "ok"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {
                "spec": {
                    "dir": "dir1",
                    "name": "test-2",
                    "json": '{ "title": "create", "uid": "1111/11111" }',
                }
            },
            (
                (
                    "change",
                    ("spec", "json"),
                    TEST_2_JSON,
                    '{ "title": "create", "uid": "1111/11111" }',
                ),
            ),
            # expected results
            "invalid_json_uid_unexpected_characters",
        ),
    ],
)
def test_update_fail(
    monkeypatch,
    fixtures_dir,
    caplog,
    json_uids,
    spec,
    status,
    old,
    new,
    diff,
    expected_error,
):
    """Test update fail."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixtures_dir)

    # set to 0 if this metric is empty
    before = (
        REGISTRY.get_sample_value(
            f"{metrics_prefix}_errors_total", {"error": expected_error}
        )
        or 0
    )

    with caplog.at_level(logging.INFO), pytest.raises(kopf.PermanentError):
        update(json_uids, MagicMock(), UID, spec, status, old, new, diff, LOGGER)

    after = REGISTRY.get_sample_value(
        f"{metrics_prefix}_errors_total", {"error": expected_error}
    )
    assert 1 == (after - before)

    assert UID in caplog.text
    # Log Level
    assert "ERROR" in caplog.text
    assert f"failed: {expected_error}" in caplog.text


@pytest.mark.parametrize(
    "json_uids, spec, status, old, new, diff, expected_updates, expected_path, expected_json, expected_log_status, expected_log_message",
    [
        # INVALID_JSON - update existing file
        (
            {},
            {"dir": "", "name": "invalid-json", "json": TEST_2_JSON},
            {"reason": "INVALID_JSON", "state": "error"},
            {"spec": {"dir": "", "name": "invalid-json", "json": INVALID_JSON}},
            {"spec": {"dir": "", "name": "invalid-json", "json": TEST_2_JSON}},
            (("change", ("spec", "json"), INVALID_JSON, TEST_2_JSON),),
            # expected results
            ["json"],
            "invalid-json.json",
            TEST_2_JSON,
            "INFO",
            "updated dashboard",
        ),
    ],
)
def test_update_error_pass_with_update(
    monkeypatch,
    fixtures_dir,
    caplog,
    json_uids,
    spec,
    status,
    old,
    new,
    diff,
    expected_updates,
    expected_path,
    expected_json,
    expected_log_status,
    expected_log_message,
):
    """Test update error fix."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixtures_dir)

    metrics_before = {}
    for metric_update in expected_updates:
        # set to 0 if this metric is empty
        metrics_before[metric_update] = (
            REGISTRY.get_sample_value(
                f"{metrics_prefix}_updated_resources_total", {"value": metric_update}
            )
            or 0
        )

    with caplog.at_level(logging.INFO):
        update(json_uids, MagicMock(), UID, spec, status, old, new, diff, LOGGER)

    for metric_update in expected_updates:
        after = REGISTRY.get_sample_value(
            f"{metrics_prefix}_updated_resources_total", {"value": metric_update}
        )
        assert 1 == (after - metrics_before[metric_update])

    assert UID in caplog.text
    assert f"fixing error for: {UID} with" in caplog.text
    assert expected_log_status in caplog.text
    assert expected_log_message in caplog.text

    p = Path(fixtures_dir, expected_path)
    assert p.is_file() is True
    assert json.loads(p.read_text()) == json.loads(expected_json)


@pytest.mark.parametrize(
    "json_uids, spec, status, old, new, diff, expected_updates, expected_path, expected_json, expected_log_status, expected_log_message",
    [
        # INVALID_JSON - create new file
        (
            {},
            {"dir": "dir2", "name": "invalid-json", "json": TEST_2_JSON},
            {"reason": "INVALID_JSON", "state": "error"},
            {"spec": {"dir": "dir2", "name": "invalid-json", "json": INVALID_JSON}},
            {"spec": {"dir": "dir2", "name": "invalid-json", "json": TEST_2_JSON}},
            (("change", ("spec", "json"), INVALID_JSON, TEST_2_JSON),),
            # expected results
            ["json"],
            "dir2/invalid-json.json",
            TEST_2_JSON,
            "INFO",
            "created dashboard",
        ),
        # duplicate_name - fix path
        (
            {},
            {"dir": "change-dir", "name": "test-2", "json": TEST_2_JSON},
            {"reason": "duplicate_name", "state": "error"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "change-dir", "name": "test-2", "json": TEST_2_JSON}},
            (("change", ("spec", "dir"), "dir1", "change-dir"),),
            # expected results
            ["dir"],
            "change-dir/test-2.json",
            TEST_2_JSON,
            "INFO",
            "created dashboard",
        ),
        # duplicate_name - fix name
        (
            {},
            {"dir": "dir1", "name": "change-name", "json": TEST_2_JSON},
            {"reason": "duplicate_name", "state": "error"},
            {"spec": {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON}},
            {"spec": {"dir": "dir1", "name": "change-name", "json": TEST_2_JSON}},
            (("change", ("spec", "name"), "test-2", "change-name"),),
            # expected results
            ["name"],
            "dir1/change-name.json",
            TEST_2_JSON,
            "INFO",
            "created dashboard",
        ),
    ],
)
def test_update_error_pass_with_create(
    monkeypatch,
    fixtures_dir,
    caplog,
    json_uids,
    spec,
    status,
    old,
    new,
    diff,
    expected_updates,
    expected_path,
    expected_json,
    expected_log_status,
    expected_log_message,
):
    """Test update error."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixtures_dir)

    before = REGISTRY.get_sample_value(f"{metrics_prefix}_created_resources_total")

    with caplog.at_level(logging.INFO):
        update(json_uids, MagicMock(), UID, spec, status, old, new, diff, LOGGER)

    after = REGISTRY.get_sample_value(f"{metrics_prefix}_created_resources_total")
    assert 1 == (after - before)

    assert UID in caplog.text
    assert f"fixing error for: {UID} with" in caplog.text
    assert expected_log_status in caplog.text
    assert expected_log_message in caplog.text

    p = Path(fixtures_dir, expected_path)
    assert p.is_file() is True
    assert json.loads(p.read_text()) == json.loads(expected_json)


@pytest.mark.parametrize(
    "spec, status, expected_deleted_path, expected_log_status, expected_log_message",
    [
        (
            {"dir": "dir1", "name": "test-2", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            # expected results
            "dir1/test-2.json",
            "INFO",
            "deleted dashboard",
        ),
        # invalid json error, no file previously created
        (
            {"dir": "dir2", "name": "invalid-json", "json": INVALID_JSON},
            {"reason": "INVALID_JSON", "state": "error"},
            # expected results
            "dir2/invalid-json.json",
            "INFO",
            "did not attempt to delete dashboard",
        ),
        # invalid json error, file exists, error from update
        (
            {"dir": "", "name": "invalid-json", "json": INVALID_JSON},
            {"reason": "INVALID_JSON", "state": "error"},
            # expected results
            "invalid-json.json",
            "INFO",
            f"fixing error for: {UID} with delete",
        ),
        # file does not exist
        (
            {"dir": "dir1", "name": "nofile", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            # expected results
            "dir1/nofile.json",
            "INFO",
            "did not attempt to delete dashboard",
        ),
    ],
)
def test_delete(
    monkeypatch,
    fixtures_dir,
    caplog,
    spec,
    status,
    expected_deleted_path,
    expected_log_status,
    expected_log_message,
):
    """Test Delete."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixture_dir)

    # set to 0 if this metric is empty
    before = REGISTRY.get_sample_value(f"{metrics_prefix}_deleted_resources_total") or 0

    with caplog.at_level(logging.INFO):
        delete(UID, spec, status, LOGGER)

    after = REGISTRY.get_sample_value(f"{metrics_prefix}_deleted_resources_total")
    assert 1 == (after - before)

    assert UID in caplog.text
    assert expected_log_status in caplog.text
    assert expected_log_message in caplog.text

    check_path = Path(fixtures_dir, expected_deleted_path)
    assert check_path.is_file() is not True


@pytest.mark.parametrize(
    "json_uids, spec, status, expected_action, expected_path, expected_json, expected_log_status, expected_log_message",
    [
        # file deleted on filesystem
        (
            {},
            {"dir": "dir1", "name": "reconcile-file", "json": TEST_2_JSON},
            {"reason": "", "state": "ok"},
            # expected results
            "create",
            "dir1/reconcile-file.json",
            TEST_2_JSON,
            "WARNING",
            "recreating missing file",
        ),
        # json drift - k8 object json is different to json on filessystem
        (
            {},
            {"dir": "dir1", "name": "test-2", "json": TEST_1_JSON},
            {"reason": "", "state": "ok"},
            # expected results
            None,
            "dir1/test-2.json",
            TEST_2_JSON,
            "WARNING",
            "json drift for",
        ),
    ],
)
def test_reconcile(
    monkeypatch,
    fixtures_dir,
    caplog,
    json_uids,
    spec,
    status,
    expected_action,
    expected_path,
    expected_json,
    expected_log_status,
    expected_log_message,
):
    """Test reconcile."""
    monkeypatch.setattr("sidecar.sidecar._working_dir", fixture_dir)

    if expected_action == "create":
        before = REGISTRY.get_sample_value(f"{metrics_prefix}_created_resources_total")

    with caplog.at_level(logging.INFO):
        reconcile(json_uids, MagicMock(), UID, spec, status, LOGGER)

    if expected_action == "create":
        after = REGISTRY.get_sample_value(f"{metrics_prefix}_created_resources_total")
        assert 1 == (after - before)

    assert UID in caplog.text
    assert expected_log_status in caplog.text
    assert expected_log_message in caplog.text

    check_path = Path(fixtures_dir, expected_path)
    assert check_path.is_file() is True
    assert json.loads(check_path.read_text()) == json.loads(expected_json)


@pytest.mark.parametrize(
    "index, expected_resource_count",
    [
        (
            {},
            0,
        ),
        (
            {
                "1": [{"dir": "dir1", "name": "test-2"}],
                "2": [{"dir": "dir2", "name": "test-3"}],
            },
            2,
        ),
    ],
)
def test_resource_count(caplog, index, expected_resource_count):
    """Test resource count."""
    with caplog.at_level(logging.INFO):
        resource_count(index, LOGGER)
        assert f"dashboard resources: {expected_resource_count}" in caplog.text


@pytest.mark.parametrize(
    "json, expected_title, expected_uid",
    [
        (
            '{"title": "test", "uid": "test"}',
            "test",
            "test",
        ),
        (
            TEST_1_JSON,
            "test-1",
            "111111111",
        ),
        (
            TEST_2_JSON,
            "test-2",
            "222222222",
        ),
    ],
)
def test_dashboard_json_meta_pass(json_str, expected_title, expected_uid):
    """Test json meta passes."""
    dashboard_uid, dashboard_title = get_dashboard_json_meta(json_str)

    assert dashboard_title == expected_title
    assert dashboard_uid == expected_uid


@pytest.mark.parametrize(
    "dashboard_json, expected_exception",
    [
        (
            '{"uid": "test"}',
            exceptions.invalidJsonNoTitle,
        ),
        (
            '{"title": "test"}',
            exceptions.invalidJsonNoUid,
        ),
        (
            "{}",
            exceptions.invalidJsonNoUid,
        ),
        (
            INVALID_JSON,
            exceptions.invalidJson,
        ),
        (
            '{"title": "test", "uid": "11111111111111111111111111111111111111111"}',
            exceptions.invalidJsonUidTooLong,
        ),
        (
            '{"title": "test", "uid": "1111`11111"}',
            exceptions.invalidJsonUidUnexpectedCharacters,
        ),
        (
            '{"title": "test`fail", "uid": "111111111"}',
            exceptions.invalidJsonTitleUnexpectedCharacters,
        ),
    ],
)
def test_dashboard_json_meta_fail(dashboard_json, expected_exception):
    """Test json meta fail exception."""
    with pytest.raises(expected_exception):
        get_dashboard_json_meta(dashboard_json)


@pytest.mark.parametrize(
    "error_index, expected_error_counts",
    [
        ({None: []}, {}),
        (
            {None: ["duplicate_name", "invalid_json", "invalid_json"]},
            {"duplicate_name": 1, "invalid_json": 2},
        ),
    ],
)
def test_error_count(caplog, error_index, expected_error_counts):
    """Tests prometheus errors count."""
    metrics_before = {}

    for error_type in expected_error_counts:
        # set to 0 if this metric is empty
        metrics_before[error_type] = (
            REGISTRY.get_sample_value(
                f"{metrics_prefix}_resource_errors", {"error": error_type}
            )
            or 0
        )

    with caplog.at_level(logging.INFO):
        error_count(error_index, LOGGER)

    for error_type, expected_count in expected_error_counts.items():
        assert f"error count (type: {error_type}): {expected_count}" in caplog.text
        after = REGISTRY.get_sample_value(
            f"{metrics_prefix}_resource_errors", {"error": error_type}
        )
        assert expected_count == (after - metrics_before[error_type])
