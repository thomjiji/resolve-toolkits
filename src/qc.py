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


class Resolve:
    def __init__(self, path: str):
        """
        path (string): media parent path, such as "素材".
        return: None
        """
        self.path = path
        self.resolve = GetResolve()
        self.project_manager = self.resolve.GetProjectManager()
        self.project = self.project_manager.GetCurrentProject()
        self.media_storage = self.resolve.GetMediaStorage()
        self.media_pool = self.project.GetMediaPool()
        self.root_folder = self.media_pool.GetRootFolder()
        self.media_fullpath_list = self.media_storage.GetSubFolderList(self.path)

    def get_all_timeline(self) -> list:
        """Get all existing timelines. Return a list containing timeline object."""
        all_timeline = []
        for timeline_index in range(1, self.project.GetTimelineCount() + 1, 1):
            all_timeline.append(self.project.GetTimelineByIndex(timeline_index))
        return all_timeline

    def get_timeline_by_name(self, timeline_name: str):
        """Get timeline object by name."""
        all_timeline = self.get_all_timeline()
        timeline_dict = {timeline.GetName(): timeline for timeline in all_timeline}
        return timeline_dict.get(timeline_name, "")

    def get_subfolder_by_name(self, subfolder_name: str):
        """Get subfolders (folder object) under the root folder in the media pool."""
        all_subfolder = self.root_folder.GetSubFolderList()
        subfolder_dict = {subfolder.GetName(): subfolder for subfolder in all_subfolder}
        return subfolder_dict.get(subfolder_name, "")

    def create_bin(self, destination_name: str, subfolders_name: list):
        """Create sub-folder in media pool."""
        destination_obj = self.get_subfolder_by_name(destination_name)
        if not destination_obj:
            print("The destination does not currently have this folder.")
        else:
            for i in subfolders_name:
                self.media_pool.AddSubFolder(destination_obj, i)

        if not self.get_subfolder_by_name("_Timeline"):
            return self.media_pool.AddSubFolder(self.root_folder, "_Timeline")


if __name__ == "__main__":
    r = Resolve('/Volumes/thom_7_for_Mac/tmp/素材')