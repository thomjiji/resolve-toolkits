from pprint import pprint
from pybmd import Bmd, toolkits
from pybmd.media_pool_item import MediaPoolItem
from pybmd.project import Project

from python_get_resolve import GetResolve
from typing import List, Union
import sys

media_path: str = sys.argv[1]

# Initialize pybmd objects
resolve = Bmd()
project_manager = resolve.get_project_manager()
project = project_manager.get_current_project()
media_storage = resolve.get_media_stroage()
media_pool = project.get_media_pool()
root_folder = media_pool.get_root_folder()
sub_folders_full_path: List[str] = media_storage.get_sub_folder_list(media_path)


def get_sub_folder_name(full_path: List[str]) -> List[str]:
    """
    Extract sub-folder name from media storage full path.
    For creating sub-folder in the media pool.
    """
    sub_folder_name: List[str] = []
    for i in full_path:
        split_full_path = i.split("/")
        sub_folder_name.append(split_full_path[-1])
    return sub_folder_name


def create_new_timeline(project: Project, timeline: str, width: str, height: str) -> None:
    """Create new timeline in the _Timeline Bin (The last folder under root folder)"""
    media_pool.set_current_folder(root_folder.get_sub_folder_list()[-1])

    # New method to check duplication of timeline.
    # Get timeline by name, return timeline object.
    existing_timeline = toolkits.get_timeline(project, timeline)
    if existing_timeline or existing_timeline.get_setting(
        'timelineResolutionWidth') == width or existing_timeline.get_setting('timelineResolutionHeight') == height:
        project.set_current_timeline(existing_timeline)

    media_pool.create_empty_timeline(timeline)
    current_timeline = project.get_current_timeline()
    current_timeline.set_setting("useCustomSettings", "1")
    current_timeline.set_setting("timelineResolutionWidth", width)
    current_timeline.set_setting("timelineResolutionHeight", height)
    current_timeline.set_setting("timelineFrameRate", str(float(25)))


def create_bin(sub_folders_full_path: list) -> None:
    """Create sub-folder in media pool."""
    sub_folders_name: List[str] = get_sub_folder_name(sub_folders_full_path)
    for i in sub_folders_name:
        media_pool.add_sub_folder(root_folder, i)
    media_pool.add_sub_folder(root_folder, "_Timeline")


def import_clip():
    """Import footage from media storage into the corresponding sub-folder of the media pool."""
    for count, sub_folder in enumerate(root_folder.GetSubFolderList()):
        media_pool.SetCurrentFolder(sub_folder)
        # 导入素材的时候排除 _Timeline 这个目的地 Bin
        if sub_folder.GetName() == "_Timeline":
            break
        media_storage.AddItemListToMediaPool(sub_folders_full_path[count])


# 3. 新建多条时间线
# 拿到机位 bin 下所有 clip 的分辨率信息，create new empty timeline.
for sub_folder in root_folder.GetSubFolderList():
    # 排除 _Timeline Bin
    if sub_folder.GetName() == "_Timeline":
        break

    # 拿到机位 bin 下所有 clip 的分辨率信息 assign to all_clips_resolution 这个 list.
    all_clips_resolution = []  # Camera 机位 bin 下所有 clip 的 resolution 信息
    for clip in sub_folder.GetClipList():
        all_clips_resolution.append(clip.GetClipProperty()["Resolution"])
    all_clips_resolution: list[str] = list(dict.fromkeys(all_clips_resolution))  # 移除 list 中的重复项

    # 根据 all_clips_resolution 里的分辨率信息新建时间线
    for res in all_clips_resolution:
        if res.split("x")[1] <= "1080":
            timeline_name = f"{sub_folder.GetName()}_{res}"
            create_new_timeline(timeline_name, res.split("x")[0], res.split("x")[1])
        else:
            clip_width = str(int(int(res.split('x')[0]) / 2))
            clip_height = str(int(int(res.split('x')[1]) / 2))
            timeline_name = f"{sub_folder.GetName()}_{clip_width}x{clip_height}"
            create_new_timeline(timeline_name, clip_width, clip_height)

# 4. 把每条素材 append 到对应的时间线
for sub_folder in root_folder.GetSubFolderList():
    # 排除 _Timeline Bin
    if sub_folder.GetName() == "_Timeline":
        break
    # if sub_folder.GetName() == "Ronin_4D#1":
    for clip in sub_folder.GetClipList():
        clip_res: str = clip.GetClipProperty()["Resolution"]
        # print(clip_res)

        timeline_number = project.GetTimelineCount()
        for i in range(timeline_number):
            existing_timeline = project.GetTimelineByIndex(i + 1)
            # print(existing_timeline.GetName())
            if existing_timeline.GetName().split("x")[1] <= "1080":
                timeline_width = existing_timeline.GetSetting()['timelineResolutionWidth']
                timeline_height = existing_timeline.GetSetting()['timelineResolutionHeight']
                # print(f"timeline_width+timeline_height: {timeline_width}x{timeline_height}")
                if clip_res == f"{timeline_width}x{timeline_height}":
                    project.SetCurrentTimeline(existing_timeline)
                    media_pool.AppendToTimeline(clip)
            else:
                timeline_width = str(int(existing_timeline.GetSetting()['timelineResolutionWidth']) * 2)
                timeline_height = str(int(existing_timeline.GetSetting()['timelineResolutionHeight']) * 2)
                if clip_res == f"{timeline_width}x{timeline_height}":
                    project.SetCurrentTimeline(existing_timeline)
                    media_pool.AppendToTimeline(clip)