from pathlib import Path

import pytest

import sidecar.exceptions as exceptions

# local library
from sidecar.dashboard_files import (
    check_file,
    create_file,
    delete_file,
    remove_empty_dir,
    update_file,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent


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
    Path(tmp_dir, "empty-dir").mkdir(parents=True, exist_ok=True)
    Path(tmp_dir, "invalid-json.json").write_text(INVALID_JSON)

    return Path(tmp_dir)


TEST_1_JSON = open_json_fixture("test-1.json")
TEST_2_JSON = open_json_fixture("dir1/test-2.json")
INVALID_JSON = "invalid json"


@pytest.mark.parametrize(
    "path, new_json",
    [
        ("test-1.json", None),
        ("test-1.json", TEST_1_JSON),
        ("dir1/test-2.json", TEST_2_JSON),
    ],
)
def test_check_file_pass(fixture_dir, path, new_json):
    check = check_file(fixture_dir, path, new_json)

    assert check is True

    p = Path(fixture_dir, path)
    assert p.is_file() is True

    if new_json is not None:
        assert p.read_text() == new_json


@pytest.mark.parametrize(
    "path, new_json, expected_exception",
    [
        ("nofile.json", None, exceptions.noFileExists),
        ("dir2/nofile.json", None, exceptions.noFileExists),
        ("test-1.json", TEST_2_JSON, exceptions.jsonMismatch),
        ("invalid-json.json", INVALID_JSON, exceptions.invalidJson),
    ],
)
def test_check_file_fail(fixture_dir, path, new_json, expected_exception):
    with pytest.raises(expected_exception):
        check_file(fixture_dir, path, new_json)


@pytest.mark.parametrize(
    "path, new_file_content",
    [
        ("create-file.json", TEST_1_JSON),
        ("dir1/create-file.json", TEST_1_JSON),
    ],
)
def test_create_file_pass(fixture_dir, path, new_file_content):
    create = create_file(fixture_dir, path, new_file_content)

    assert create is True

    p = Path(fixture_dir, path)
    assert p.is_file() is True
    assert p.read_text() == new_file_content


@pytest.mark.parametrize(
    "path, new_file_content, expected_exception",
    [
        ("test-1.json", TEST_1_JSON, exceptions.duplicateName),
        ("dir1/test-2.json", TEST_2_JSON, exceptions.duplicateName),
        ("invalid-json-new.json", INVALID_JSON, exceptions.invalidJson),
        (
            "dir2/dir-not-exist/parent-dir-not-exist.json",
            TEST_1_JSON,
            exceptions.parentDirDoesNotExist,
        ),
    ],
)
def test_create_file_fail(fixture_dir, path, new_file_content, expected_exception):
    with pytest.raises(expected_exception):
        create_file(fixture_dir, path, new_file_content)


@pytest.mark.parametrize(
    "old_path, new_path, new_json",
    [
        (
            "test-1.json",
            "change-name.json",
            None,
        ),
        (
            "dir1/test-2.json",
            "change-dir/test-2.json",
            None,
        ),
        (
            "test-1.json",
            None,
            TEST_2_JSON,
        ),
    ],
)
def test_update_file_pass(fixture_dir, old_path, new_path, new_json):
    update = update_file(fixture_dir, old_path, new_path, new_json)

    assert update is True

    path = new_path if new_path is not None else old_path
    path = Path(fixture_dir, path)

    assert path.is_file() is True

    if new_json is not None:
        assert path.read_text() == new_json


@pytest.mark.parametrize(
    "old_path, new_path, new_json, expected_exception",
    [
        (None, None, None, exceptions.nothingToDo),
        ("test-1.json", "test-1.json", None, exceptions.nothingToDo),
        ("nofile.json", "not-exist.json", None, exceptions.oldPathDoesNotExist),
        ("test-1.json", None, "invalid-json.json", exceptions.invalidJson),
        ("test-1.json", "dir1/test-2.json", None, exceptions.duplicateName),
    ],
)
def test_update_file_fail(
    fixture_dir, old_path, new_path, new_json, expected_exception
):
    with pytest.raises(expected_exception):
        update_file(fixture_dir, old_path, new_path, new_json)


@pytest.mark.parametrize(
    "path",
    [
        ("test-1.json"),
        ("dir1/test-2.json"),
    ],
)
def test_delete_file_pass(fixture_dir, path):
    delete = delete_file(fixture_dir, path)

    assert delete is True
    assert Path(fixture_dir, path).is_file() is False


@pytest.mark.parametrize(
    "path, expected_exception",
    [
        ("dir1/nofile", exceptions.noFileExists),
        ("nodir", exceptions.noFileExists),
    ],
)
def test_delete_file_fail(fixture_dir, path, expected_exception):
    with pytest.raises(expected_exception):
        delete_file(fixture_dir, path)


@pytest.mark.parametrize(
    "path",
    [
        ("empty-dir"),
    ],
)
def test_remove_empty_dir_pass(fixture_dir, path):
    path = Path.cwd().joinpath(fixture_dir, path)
    rmdir = remove_empty_dir(path)

    assert rmdir is True
    assert Path(fixture_dir, path).is_dir() is False


@pytest.mark.parametrize(
    "path, expected_exception",
    [
        ("", exceptions.dirNotEmpty),
        ("dir1", exceptions.dirNotEmpty),
        ("same-json.json", exceptions.pathNotDir),
    ],
)
def test_remove_empty_dir_fail(fixture_dir, path, expected_exception):
    path = Path.cwd().joinpath(fixture_dir, path)

    with pytest.raises(expected_exception):
        remove_empty_dir(path)
