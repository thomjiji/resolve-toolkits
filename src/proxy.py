#!/usr/bin/env python3

# Import modules for Resolve native API
import argparse
import os
import sys
import logging
from typing import List
from resolve_init import GetResolve

INVALID_EXTENSION = ["DS_Store", "JPG", "JPEG", "SRT"]

# Set up logger
log = logging.getLogger("proxy_logger")
log.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(
    "%(levelname)s - %(asctime)s - %(name)s: %(message)s", datefmt="%H:%M:%S"
)

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
log.addHandler(ch)


def absolute_file_paths(path: str) -> list:
    absolute_file_path_list = []
    for directory_path, _, filenames in os.walk(path):
        for filename in filenames:
            absolute_file_path_list.append(
                os.path.abspath(os.path.join(directory_path, filename))
            )
    return absolute_file_path_list


def get_subfolders_name(source_media_full_path: List[str]) -> List[str]:
    """
    Extract sub-folder name from media storage full path.
    For creating sub-folder in the media pool.
    """
    return [os.path.split(i)[1] for i in source_media_full_path]


def get_sorted_path(path: str) -> list:
    """
    Get the absolute paths of all files from the given path, then sort the absolute paths,
    and finally return a list of sorted absolute paths.
    """
    filename_and_fullpath_dict = {
        os.path.basename(os.path.splitext(path)[0]): path
        for path in absolute_file_paths(path)
        if os.path.splitext(path)[-1].replace(".", "") not in INVALID_EXTENSION
    }
    filename_and_fullpath_keys = list(filename_and_fullpath_dict.keys())
    filename_and_fullpath_keys.sort()
    filename_and_fullpath_value = [
        filename_and_fullpath_dict.get(i) for i in filename_and_fullpath_keys
    ]
    return filename_and_fullpath_value


class Resolve:
    def __init__(self, input_path: str, output_path=None):
        self.media_parent_path = input_path
        self.proxy_parent_path = output_path
        self.resolve = GetResolve()
        self.project_manager = self.resolve.GetProjectManager()
        self.project = self.project_manager.GetCurrentProject()
        self.media_storage = self.resolve.GetMediaStorage()
        self.media_pool = self.project.GetMediaPool()
        self.root_folder = self.media_pool.GetRootFolder()
        self.timeline = self.project.GetCurrentTimeline()
        self.media_fullpath_list = self.media_storage.GetSubFolderList(self.media_parent_path)

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

    def create_bin(self, subfolders_name: list):
        """Create sub-folder in the media pool root folder."""
        for i in subfolders_name:
            self.media_pool.AddSubFolder(self.root_folder, i)

        if not self.get_subfolder_by_name("_Timeline"):
            return self.media_pool.AddSubFolder(self.root_folder, "_Timeline")

    def import_clip(self, one_by_one=False) -> None:
        """
        Import footage from media storage into the corresponding subfolder of the media
        pool root folder. Filter out the files with suffix in the INVALID_EXTENSION list
        before importing. If one_by_one parameter is specified as True, then it will be
        imported one by one, which is relatively slow.

        Args:
            path (string): source media parent path, such as "素材".

        Returns:
            None
        """
        media_parent_dir = os.path.basename(self.media_parent_path)

        if not one_by_one:
            for cam_path in self.media_fullpath_list:
                filename_and_fullpath_value = get_sorted_path(cam_path)
                if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
                    name = cam_path.split("\\")[
                        cam_path.split("\\").index(media_parent_dir) + 1
                        ]
                    current_folder = self.get_subfolder_by_name(name)
                else:
                    current_folder = self.get_subfolder_by_name(
                        f"{cam_path.split('/')[cam_path.split('/').index(media_parent_dir) + 1]}"
                    )

                self.media_pool.SetCurrentFolder(current_folder)
                self.media_storage.AddItemListToMediaPool(filename_and_fullpath_value)
        else:
            for abs_media_path in get_sorted_path(self.media_parent_path):
                if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
                    name = abs_media_path.split("\\")[
                        abs_media_path.split("\\").index(media_parent_dir) + 1
                        ]
                    current_folder = self.get_subfolder_by_name(name)
                else:
                    current_folder = self.get_subfolder_by_name(
                        f"{abs_media_path.split('/')[abs_media_path.split('/').index(media_parent_dir) + 1]}"
                    )

                self.media_pool.SetCurrentFolder(current_folder)
                self.media_pool.ImportMedia(abs_media_path)

    def get_resolution(self) -> list:
        """Get all clips resolution, return a list consist of all resolution string."""
        all_clips_resolution = []
        for bin in self.root_folder.GetSubFolderList():
            # 排除 _Timeline bin
            if bin.GetName() == "_Timeline":
                break

            for clip in bin.GetClipList():
                all_clips_resolution.append(clip.GetClipProperty("Resolution"))
            all_clips_resolution = list(dict.fromkeys(all_clips_resolution))

        return all_clips_resolution

    def create_and_change_timeline(
        self, timeline_name: str, width: str, height: str
    ) -> None:
        """
        Simply create empty timeline and change its resolution to inputs width and height.
        Used for create_new_timeline() function.
        """
        self.media_pool.CreateEmptyTimeline(timeline_name)
        current_timeline = self.project.GetCurrentTimeline()
        current_timeline.SetSetting("useCustomSettings", "1")
        current_timeline.SetSetting("timelineResolutionWidth", str(width))
        current_timeline.SetSetting("timelineResolutionHeight", str(height))
        current_timeline.SetSetting("timelineFrameRate", str(25))

    def create_new_timeline(self, timeline_name: str, width: int, height: int) -> bool:
        """
        Create new timeline in the _Timeline bin (the last folder under root folder).
        Check timeline duplication.

        :param timeline_name: The name of the timeline that will be created
        :param width: The width of the timeline that will be created
        :param height: The height of the timeline that will be created
        :type timeline_name: str
        :type width: int
        :type height: int
        """
        self.media_pool.SetCurrentFolder(
            self.root_folder.GetSubFolderList()[-1]
        )  # SetCurrentFolder 到 _Timeline bin 把时间线都建在这

        if self.project.GetTimelineCount() == 0:
            self.create_and_change_timeline(timeline_name, str(width), str(height))
            return True
        else:
            existing_timeline_resolution = []
            for existing_timeline in self.get_all_timeline():
                existing_timeline_resolution.append(
                    f"{existing_timeline.GetSetting('timelineResolutionWidth')}x{existing_timeline.GetSetting('timelineResolutionHeight')}"
                )
            if f"{str(width)}x{str(height)}" not in existing_timeline_resolution:
                self.create_and_change_timeline(timeline_name, str(width), str(height))
            else:
                current_timeline = self.project.GetCurrentTimeline()
                new_name = f"{current_timeline.GetName()}_{str(width)}x{str(height)}"
                current_timeline.SetName(new_name)

    def append_to_timeline(self) -> None:
        """Append to timeline"""
        all_timeline_name = [timeline.GetName() for timeline in self.get_all_timeline()]
        for subfolder in self.root_folder.GetSubFolderList():
            for clip in subfolder.GetClipList():
                if (
                    clip.GetClipProperty("type") == "Video"
                    or clip.GetClipProperty("type") == "Video + Audio"
                ):
                    clip_width = clip.GetClipProperty("Resolution").split("x")[0]
                    clip_height = clip.GetClipProperty("Resolution").split("x")[1]
                    for name in all_timeline_name:
                        if f"{clip_width}x{clip_height}" in name:
                            self.project.SetCurrentTimeline(
                                self.get_timeline_by_name(name)
                            )
                            self.media_pool.AppendToTimeline(clip)

    def add_render_job(self):
        """Select a render preset, set the render path, add to render queue."""
        preset_list = self.project.GetRenderPresetList()
        if len(preset_list) < 32:
            print("Please pour in the H.265 render preset first.")
        elif len(preset_list) > 33:
            print("There are too many custom render presets, please specify it.")
        else:
            # 加载 H.265 渲染预设.
            proxy_preset = preset_list[-1]
            self.project.LoadRenderPreset(proxy_preset)

            # 把时间线分别添加到渲染队列
            for timeline in self.get_all_timeline():
                self.project.SetCurrentTimeline(timeline)
                try:
                    os.mkdir(f"{self.proxy_parent_path}/{timeline.GetName()}")
                except FileExistsError:
                    pass
                rendering_setting = {
                    "TargetDir": f"{self.proxy_parent_path}/{timeline.GetName()}"
                }
                self.project.SetRenderSettings(rendering_setting)
                self.project.AddRenderJob()

    def set_project_color_management(self):
        """
        If the running platform is Mac OS, set the project color management to
        DaVinci YRGB and the timeline color space to Rec.709 Gamma 2.4. If the platform
        is Windows, set the timeline color space to
        """
        if sys.platform.startswith("darwin"):
            self.project.SetSetting('colorScienceMode', 'davinciYRGB')
            self.project.SetSetting('colorSpaceTimeline', 'Rec.709 Gamma 2.4')
            self.project.SetSetting('colorSpaceOutput', 'Same as Timeline')


if __name__ == "__main__":

    # Get commandline arguments
    parser = argparse.ArgumentParser(
        description="Proxy is a commandline tool to automatic import clips, create timelines, add to render queue "
                    "using the predefined preset quickly and easily.")
    parser.add_argument('input',
                        help='Input path of media.',
                        action='store',
                        type=str)
    parser.add_argument('output',
                        help='Output path of proxy rendering.',
                        action='store',
                        type=str)
    args = parser.parse_args()

    # show help if no args
    if len(sys.argv) == 1:
        parser.print_help()

    media_parent_path = args.input
    if not os.path.exists(args.output):
        log.debug(f"'{args.output}' doesn't exist, please ensure this directory exists.\n")
        parser.print_help()
        sys.exit()
    else:
        proxy_parent_path = args.output

    r = Resolve(media_parent_path, proxy_parent_path)
    r.set_project_color_management()

    # 从 media storage 得到 bin 名称之后，以此在 media pool 分辨新建对应的 bin。导入素材到对应的 bin。
    subfolders_name = get_subfolders_name(r.media_fullpath_list)
    r.create_bin(subfolders_name)
    r.import_clip()

    # 根据媒体池所有的素材分辨率新建不同的时间线。
    for res in r.get_resolution():
        if "x" not in res:
            continue
        if int(res.split("x")[1]) <= 1080:
            timeline_width = res.split("x")[0]
            timeline_height = res.split("x")[1]
            r.create_new_timeline(res, timeline_width, timeline_height)
        else:
            timeline_width = int(int(res.split("x")[0]) / 2)
            timeline_height = int(int(res.split("x")[1]) / 2)
            r.create_new_timeline(res, timeline_width, timeline_height)

    # 导入素材到对应时间线
    r.append_to_timeline()

    # 将所有时间线以 H.265 的渲染预设添加到渲染队列
    r.add_render_job()

    # 开始渲染之前，暂停程序，向用户确认是否有添加 Burn-in，同时给用户时间确认其他参数是否正确。然后开始渲染。
    if input("The program is paused, please add burn-in manually, then enter 'y' to start rendering. Enter 'n' to "
             "exit the program. y/n?") == "y":
        r.project.StartRendering(isInteractiveMode=True)

    # for render_job in project.GetRenderJobList():
    #     pprint(render_job)

    # # Job status check
    # job_id_list = [render_job.get('JobId') for render_job in project.GetRenderJobList()]
    # print(project.GetRenderJobStatus(job_id_list[1]))