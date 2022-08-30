import re
import sys
from typing import List
import os.path
from pprint import pprint
from resolve_init import GetResolve
from proxy import Resolve


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


class QC(Resolve):
    def __init__(self, path: str):
        super().__init__(path)

    def create_and_change_timeline(self, timeline_name: str, width: str, height: str, fps: float) -> None:
        """
        Simply create empty timeline and change its resolution to inputs width and height.
        Used for create_new_timeline() function.
        """
        self.media_pool.CreateEmptyTimeline(timeline_name)
        current_timeline = self.project.GetCurrentTimeline()
        current_timeline.SetSetting("useCustomSettings", "1")
        current_timeline.SetSetting("timelineResolutionWidth", str(width))
        current_timeline.SetSetting("timelineResolutionHeight", str(height))
        current_timeline.SetSetting("timelineFrameRate", str(fps))

    def create_timeline_qc(self):
        for subfolder in self.root_folder.GetSubFolderList():
            for folder in subfolder.GetSubFolderList():
                self.media_pool.SetCurrentFolder(folder)
                res_fps_dict = self.get_bin_resolution(subfolder.GetName())
                for k, v in res_fps_dict.items():
                    timeline_name = f"{subfolder.GetName()}_{k}_{v}"
                    self.create_and_change_timeline(timeline_name, k.split('x')[0], k.split('x')[1], v)

    def get_bin_resolution(self, bin_name: str):
        current_bin = self.get_subfolder_by_name(bin_name)
        bin_res_fps_dict = {clip.GetClipProperty('Resolution'): clip.GetClipProperty('FPS') for clip in
                            current_bin.GetClipList()}

        return bin_res_fps_dict

    def create_bin(self, subfolders_name: list):
        """Create _Timeline bin under each camera bin in the media pool."""
        for i in subfolders_name:
            self.media_pool.AddSubFolder(self.root_folder, i)
            if is_camera_dir(i):
                self.media_pool.AddSubFolder(self.get_subfolder_by_name(i), "_Timeline")


if __name__ == '__main__':
    # 检查用户是否提供了正确的 argv。
    if len(sys.argv) < 2:
        print("Usage: python3 qc.py [media path]. \nPlease ensure this directory exist.")
        sys.exit()
    else:
        media_parent_path: str = sys.argv[1]

    r = QC(media_parent_path)

    # # 从 media storage 得到 bin 名称之后，以此在 media pool 分辨新建对应的 bin。导入素材到对应的 bin。
    # subfolders_name = get_subfolders_name(r.media_fullpath_list)
    # r.create_bin(subfolders_name)
    # r.import_clip()
    #
    # # 导入素材到对应时间线
    # r.append_to_timeline()

    # print(r.get_bin_resolution('Ronin_4D#2'))
    print(r.create_timeline_qc())