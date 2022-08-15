from pprint import pprint

from pybmd.media_pool_item import MediaPoolItem
from python_get_resolve import GetResolve
from typing import List, Union
import sys

media_path: str = sys.argv[1]

resolve = GetResolve()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_storage = resolve.GetMediaStorage()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()
sub_folders_full_path: List[str] = media_storage.GetSubFolderList(media_path)


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


def create_new_timeline(timeline: str, width: str, height: str) -> None:
    """Create new timeline in the _Timeline Bin (The last folder under root folder)"""
    media_pool.SetCurrentFolder(root_folder.GetSubFolderList()[-1])
    timeline_number = project.GetTimelineCount()
    for i in range(timeline_number):
        existing_timeline = project.GetTimelineByIndex(i + 1)
        if existing_timeline.GetName() == timeline or existing_timeline.GetSetting()[
            'timelineResolutionWidth'] == width and existing_timeline.GetSetting()[
            'timelineResolutionHeight'] == height:
            project.SetCurrentTimeline(existing_timeline)

    media_pool.CreateEmptyTimeline(timeline)
    current_timeline = project.GetCurrentTimeline()
    current_timeline.SetSetting("useCustomSettings", "1")
    current_timeline.SetSetting("timelineResolutionWidth", width)
    current_timeline.SetSetting("timelineResolutionHeight", height)
    current_timeline.SetSetting("timelineFrameRate", str(float(25)))


# 1. Create sub-folder in media pool.
sub_folders_name: List[str] = get_sub_folder_name(sub_folders_full_path)
for i in sub_folders_name:
    media_pool.AddSubFolder(root_folder, i)
media_pool.AddSubFolder(root_folder, "_Timeline")

# 2. Import footage from media storage into the corresponding sub-folder of the media pool.
for count, sub_folder in enumerate(root_folder.GetSubFolderList()):
    media_pool.SetCurrentFolder(sub_folder)
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