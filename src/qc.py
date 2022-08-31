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
        self.camera_log_dict = {
            'S-Gamut3.Cine/S-Log3': ['A7S3', 'FX3', 'FX6', 'FX9', 'FS7', 'Z90'],
            'Panasonic V-Gamut/V-Log': ['GH5', 'GH5M2', 'S1H', 'GH5S', 'S5'],
            'ARRI LogC3': ['ALEXA_Mini', 'ALEXA_Mini_LF', 'AMIRA'],
            'ARRI LogC4': ['ALEXA 35'],
            'DJI D-Gamut/D-Log': ['Ronin_4D', '航拍', 'Mavic', 'MavicPro'],
            'Rec.709 Gamma 2.4': ['Others']
        }

    def create_and_change_timeline(self, timeline_name: str, width: str, height: str, fps: int) -> None:
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
        """
        In the _Timeline bin under each bin of the media pool, create a new
        timeline based on the resolution and frame rate of the clip under that
        bin.

        :return: None
        """
        for subfolder in self.root_folder.GetSubFolderList():
            for folder in subfolder.GetSubFolderList():
                self.media_pool.SetCurrentFolder(folder)
                res_fps_dict = self.get_bin_res_and_fps(subfolder.GetName())
                for res, fps in res_fps_dict.items():
                    timeline_name = f"{subfolder.GetName()}_{res}_{int(fps)}p"
                    self.create_and_change_timeline(timeline_name, res.split('x')[0], res.split('x')[1], int(fps))

    def get_bin_res_and_fps(self, bin_name: str):
        """
        Get the resolution and frame rate of all clips under the given bin_name,
        return a dict.

        :param bin_name: 媒体池已有的 camera bin
        :return: 包含了媒体池该 camera bin 下所有素材的分辨率帧率的 dict，给 create_timeline_qc 使用
        """
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

    def append_to_timeline(self) -> None:
        for subfolder in self.root_folder.GetSubFolderList():
            self.media_pool.SetCurrentFolder(subfolder)
            for clip in subfolder.GetClipList():
                if clip.GetClipProperty("type") == "Video" or clip.GetClipProperty("type") == "Video + Audio":
                    res = clip.GetClipProperty('Resolution')
                    fps = clip.GetClipProperty('FPS')
                    current_timeline = self.get_timeline_by_name(f"{subfolder.GetName()}_{res}_{int(fps)}p")
                    if not self.project.SetCurrentTimeline(current_timeline):
                        print("append_to_timeline() project.SetCurrentTimeline failed.")
                    self.media_pool.AppendToTimeline(clip)
                    self.set_clip_colorspace(clip)

    def set_project_color_management(self):
        self.project.SetSetting('colorScienceMode', 'davinciYRGBColorManagedv2')
        self.project.SetSetting('isAutoColorManage', '0')
        self.project.SetSetting('colorSpaceTimeline', 'DaVinci WG/Intermediate')
        self.project.SetSetting('colorSpaceInput', 'Rec.709 Gamma 2.4')
        self.project.SetSetting('colorSpaceOutput', 'Rec.709 Gamma 2.4')
        self.project.SetSetting('timelineWorkingLuminanceMode', 'SDR 100')
        self.project.SetSetting('timelineWorkingLuminanceMode', 'SDR 100')
        self.project.SetSetting('inputDRT', 'DaVinci')
        self.project.SetSetting('outputDRT', 'DaVinci')
        self.project.SetSetting('useCATransform', '1')
        self.project.SetSetting('useColorSpaceAwareGradingTools', '1')

    def set_clip_colorspace(self, clip):
        clip_path = clip.GetClipProperty('File Path')
        cam_name = clip_path.split('/')[clip_path.split('/').index(os.path.basename(r.path)) + 1].split('#')[0]
        camera_log_key = list(self.camera_log_dict.keys())
        camera_log_val = list(self.camera_log_dict.values())
        try:
            position = camera_log_val.index([value for value in camera_log_val if cam_name in value][0])
            color_space = camera_log_key[position]
        except IndexError:
            color_space = camera_log_key[-1]
        if clip.SetClipProperty('Input Color Space', color_space):
            print(f"Set input color space {color_space} for {clip.GetName()} succeed.")


if __name__ == '__main__':
    # 检查用户是否提供了正确的 argv。
    if len(sys.argv) < 2:
        print("Usage: python3 qc.py [media path]. \nPlease ensure this directory exist.")
        sys.exit()
    else:
        media_parent_path: str = sys.argv[1]

    r = QC(media_parent_path)

    # 从 media storage 得到 bin 名称之后，以此在 media pool 分辨新建对应的 bin。导入素材到对应的 bin
    subfolders_name = get_subfolders_name(r.media_fullpath_list)
    r.create_bin(subfolders_name)
    r.import_clip(one_by_one=True)

    # 创建基于 media pool 下各 camera bin 里素材的分辨率帧率的时间线
    r.create_timeline_qc()

    # 导入素材到对应时间线
    r.append_to_timeline()

    r.set_project_color_management()