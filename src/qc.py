import re
from typing import List
import os.path
from pprint import pprint
from resolve_init import GetResolve


def absolute_file_paths(path: str) -> list:
    """Get the absolute paths of all files under a given path."""
    absolute_file_path_list = []
    for directory_path, _, filenames in os.walk(path):
        for f in filenames:
            if f.split('.')[-1] != "DS_Store":
                absolute_file_path_list.append(os.path.abspath(os.path.join(directory_path, f)))
    return absolute_file_path_list


def get_subfolders_name(path: List[str]) -> List[str]:
    """
    Extract sub-folder name from media storage full path.
    For creating sub-folder in the media pool.

    args:
        path: the next directory level of current media storage path lists.

    return:
        List: containing subfolders name.
    """
    return [os.path.split(i)[1] for i in path]


def is_camera_dir(text: str) -> bool:
    matched = re.search(r"^.+#\d$", text)
    if matched:
        return True
    else:
        return False