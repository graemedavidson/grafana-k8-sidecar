import json
from pathlib import Path

# Local Libraries
import sidecar.exceptions as exceptions


def validate_json(jsonData: str) -> bool:
    try:
        json.loads(jsonData)
    except ValueError:
        return False
    return True


def check_file(working_dir: str, path: str, dashboard_json: str = "") -> bool:
    """
    Checks a dashboard exists and has correct content
    """

    full_path = Path.cwd().joinpath(working_dir, path)

    if not full_path.is_file():
        raise exceptions.noFileExists

    if dashboard_json:
        if not validate_json(dashboard_json):
            raise exceptions.invalidJson

        if full_path.read_text() != dashboard_json:
            raise exceptions.jsonMismatch

    return True


def create_file(working_dir: str, path: str, dashboard_json: str):
    """
    Create a dashboard file, mkdir if does not exist
    """

    full_path = Path.cwd().joinpath(working_dir, path)

    if Path(full_path).is_file():
        raise exceptions.duplicateName

    if not validate_json(dashboard_json):
        raise exceptions.invalidJson

    try:
        full_path.parents[0].mkdir(parents=False, exist_ok=True)
        full_path.write_text(dashboard_json)
    except FileNotFoundError:
        raise exceptions.parentDirDoesNotExist
    except PermissionError:
        raise exceptions.incorrect_permissions

    return True


def update_file(
    working_dir: str, old_path: str, new_path: str = "", new_json: str = ""
):
    """
    update a dashboard file by name, dir, and json content
    """

    path_change = False
    if new_path != "" and old_path != new_path:
        path_change = True

    if not path_change and new_json == "":
        raise exceptions.nothingToDo

    full_old_path = Path(working_dir, old_path)

    if not Path(full_old_path).is_file():
        raise exceptions.oldPathDoesNotExist

    if new_json != "" and not validate_json(new_json):
        raise exceptions.invalidJson

    if new_json != "":
        full_old_path.write_text(new_json)

    if path_change:
        full_new_path = Path(working_dir, new_path)

        if full_new_path.is_file():
            # error: duplicate name, but still delete old file as this can disrupt other operations
            full_old_path.unlink()
            try:
                remove_empty_dir(full_old_path.parents[0])
            except exceptions.pathNotDir:
                pass
            except exceptions.dirNotEmpty:
                pass
            except Exception:
                # ToDo: Should log this as unexpected exception.
                pass
            raise exceptions.duplicateName

        full_new_path.parents[0].mkdir(parents=False, exist_ok=True)
        full_old_path.rename(full_new_path)

        try:
            remove_empty_dir(full_old_path.parents[0])
        except exceptions.pathNotDir:
            pass
        except exceptions.dirNotEmpty:
            pass
        except Exception:
            # ToDo: Should log this as unexpected exception.
            pass

    return True


def delete_file(working_dir: str, path: str) -> bool:
    """
    delete a dashboard and remove dir if then empty
    """

    full_path = Path.cwd().joinpath(working_dir, path)

    if not Path(full_path).is_file():
        raise exceptions.noFileExists

    full_path.unlink()

    try:
        remove_empty_dir(full_path.parents[0])
    except exceptions.pathNotDir:
        pass
    except exceptions.dirNotEmpty:
        pass
    except Exception:
        # ToDo: Should log this as unexpected exception.
        pass

    return True


def remove_empty_dir(path: Path) -> bool:
    """remove path if no files (dashboards exist in it)"""

    if not path.is_dir():
        raise exceptions.pathNotDir

    if any(path.iterdir()):
        raise exceptions.dirNotEmpty

    path.rmdir()

    return True
