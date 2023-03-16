class Exception(Exception):
    """Base class for other exceptions"""

    def __init__(self):
        """Exception message parameters."""
        self.message = None
        self.code = None

    def __str__(self):
        """Return error message."""
        return str(self.message)


class jsonTitleMatchesDirName(Exception):
    def __init__(self):
        """Dashboard json title field matches kubernetes resource dir name."""
        self.message = "dashboard json title field matches kubernetes resource dir name"
        self.code = "json_title_matches_dir_name"


class invalidJson(Exception):
    def __init__(self):
        """JSON passed has invalid syntax."""
        self.message = "json passed has invalid syntax"
        self.code = "invalid_json"


class invalidJsonNoUid(Exception):
    def __init__(self):
        """Dashboard json is missing the uid field."""
        self.message = "dashboard json is missing the uid field"
        self.code = "invalid_json_no_uid"


class invalidJsonUidTooLong(Exception):
    def __init__(self):
        """Dashboard json uid field is greater than 40 characters."""
        self.message = "dashboard json uid field is greater than 40 characters"
        self.code = "invalid_json_uid_too_long"


class invalidJsonUidUnexpectedCharacters(Exception):
    def __init__(self):
        """Dashboard json uid field includes unexpected characters."""
        self.message = "dashboard json uid field includes unexpected characters"
        self.code = "invalid_json_uid_unexpected_characters"


class duplicateDashboardUid(Exception):
    def __init__(self):
        """UID in the dashboard json used by another dashboard."""
        self.message = "uid in the dashboard json used by another dashboard"
        self.code = "duplicate_dashboard_uid"


class invalidJsonNoTitle(Exception):
    def __init__(self):
        """Dashboard json is missing the title field."""
        self.message = "dashboard json is missing the title field"
        self.code = "invalid_json_no_title"


class invalidJsonTitleUnexpectedCharacters(Exception):
    def __init__(self):
        """Dashboard json title field includes unexpected characters."""
        self.message = "dashboard json title field includes unexpected characters"
        self.code = "invalid_json_title_unexpected_characters"


class nothingToDo(Exception):
    def __init__(self):
        """No changes found when comparing File system dashboard and Kubernetes resource."""
        self.message = "No changes found when comparing File system dashboard and Kubernetes resource"
        self.code = "nothing_to_do"


class noFileExists(Exception):
    def __init__(self):
        """When attempting a check or delete of dashboard the expected file is not found on the file system."""
        self.message = "when attempting a check or delete of dashboard the expected file is not found on the file system"
        self.code = "no_file_exists"


class jsonMismatch(Exception):
    def __init__(self):
        """JSON on the filesystem is different from the kubernetes resource."""
        self.message = (
            "json on the filesystem is different from the kubernetes resource"
        )
        self.code = "json_mismatch"


class duplicateName(Exception):
    def __init__(self):
        """Dir/Name fields in kubernetes resource is used by another resource."""
        self.message = (
            "dir/name fields in kubernetes resource is used by another resource"
        )
        self.code = "duplicate_name"


class parentDirDoesNotExist(Exception):
    def __init__(self):
        """Dir field in kubernetes resource does not exist."""
        self.message = "dir field in kubernetes resource does not exist"
        self.code = "parent_dir_does_not_exist"


class incorrect_permissions(Exception):
    def __init__(self):
        """K8 grafana sidecar does not have permissions to write to file system."""
        self.message = (
            "k8 grafana sidecar does not have permissions to write to file system"
        )
        self.code = "incorrect_permissions"


class oldPathDoesNotExist(Exception):
    def __init__(self):
        """When updating dashboard the old path does not exist on file system."""
        self.message = (
            "when updating dashboard the old path does not exist on file system"
        )
        self.code = "old_path_does_not_exist"


class pathNotDir(Exception):
    def __init__(self):
        """Dir field in kubernetes resource is not a directory on the file system (is a file)."""
        self.message = "dir field in kubernetes resource is not a directory on the file system (is a file)"
        self.code = "path_not_dir"


class dirNotEmpty(Exception):
    def __init__(self):
        """When attempting to delete a directory it is found not empty."""
        self.message = "when attempting to delete a directory it is found not empty"
        self.code = "dir_not_empty"
