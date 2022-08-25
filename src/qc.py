import sys

from resolve_init import GetResolve
from proxy import get_subfolder_name, create_bin
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


media_parent_path = sys.argv[1]
resolve = Resolve(media_parent_path)
print(resolve.project.GetName())