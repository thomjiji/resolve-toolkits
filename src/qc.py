from typing import List
import os.path
import sys
from pprint import pprint
from resolve_init import GetResolve
from proxy import get_subfolder_name, create_bin
from proxy import INVALID_EXTENSION


# from resolve_init import DaVinciResolveScript as bmd


class Resolve:
    def __init__(self, path: str):
        """
        param path: media parent path, such as "素材".
        return: None
        """
        # self.resolve = bmd.scriptapp('Resolve')
        self.path = path
        self.resolve = GetResolve()
        self.project_manager = self.resolve.GetProjectManager()
        self.project = self.project_manager.GetCurrentProject()
        self.media_storage = self.resolve.GetMediaStorage()
        self.media_pool = self.project.GetMediaPool()
        self.root_folder = self.media_pool.GetRootFolder()
        self.media_fullpath_list = self.media_storage.GetSubFolderList(self.path)

    def absolute_file_paths(self, path: str) -> list:
        absolute_file_path_list = []
        for directory_path, _, filenames in os.walk(path):
            for f in filenames:
                absolute_file_path_list.append(os.path.abspath(os.path.join(directory_path, f)))
        return absolute_file_path_list

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

    def create_and_import(self):
        for folder_path in self.media_storage.GetSubFolderList(self.path):
            self.media_pool.AddSubFolder(self.root_folder, os.path.split(folder_path)[1])
            print(folder_path)
            for i in self.media_storage.GetSubFolderList(folder_path):
                print(i)
                for j in self.media_storage.GetSubFolderList(i):
                    print(j)

    def create_bin(self, subfolders_name: list, destination_name: str) -> None:
        """Create sub-folder in media pool."""
        for i in subfolders_name:
            self.media_pool.AddSubFolder(destination_name, i)
        if not get_subfolder_name("_Timeline"):
            self.media_pool.AddSubFolder(self.root_folder, "_Timeline")


media_parent_path = sys.argv[1]
resolve = Resolve(media_parent_path)

media_fullpath_list = resolve.media_storage.GetSubFolderList(media_parent_path)
pprint(media_fullpath_list)
subfolder_name_list = resolve.get_subfolders_name(media_fullpath_list)
print(subfolder_name_list)